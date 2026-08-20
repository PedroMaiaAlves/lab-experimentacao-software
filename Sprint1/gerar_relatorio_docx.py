"""Gera o relatório Lab01S02 em DOCX a partir do template e do CSV validado."""

from __future__ import annotations

import argparse
import tempfile
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor


BASE_DIR = Path(__file__).resolve().parent
CSV_PADRAO = BASE_DIR / "data" / "raw" / "repositorios_populares.csv"
SAIDA_PADRAO = BASE_DIR / "docs" / "Relatorio_Lab01S02.docx"
TEMPLATE_PADRAO = (
    Path.home() / "Downloads" / "Template_Relatorio_Laboratorio.docx"
)

AZUL = "1F3A5F"
VERDE = "1F6E63"
VERDE_GRAFICO = "#0F766E"
LARANJA_GRAFICO = "#D97706"
CINZA_GRAFICO = "#6B7280"
CINZA_CLARO = "F0F0EC"
BRANCO = "FFFFFF"
TEXTO = "202020"


def limpar_corpo(documento: Document) -> None:
    """Remove o conteúdo do template, preservando estilos e propriedades da seção."""

    body = documento._element.body
    for filho in list(body):
        if filho.tag != qn("w:sectPr"):
            body.remove(filho)


def configurar_estilos(documento: Document) -> None:
    normal = documento.styles["Normal"]
    normal.font.name = "Calibri"
    normal.font.size = Pt(11)
    normal.font.color.rgb = RGBColor.from_string(TEXTO)
    normal.paragraph_format.space_after = Pt(6)
    normal.paragraph_format.line_spacing = 1.15

    titulo = documento.styles["Title"]
    titulo.font.name = "Calibri"
    titulo.font.size = Pt(26)
    titulo.font.bold = True
    titulo.font.color.rgb = RGBColor.from_string("17365D")

    subtitulo = documento.styles["Subtitle"]
    subtitulo.font.name = "Calibri"
    subtitulo.font.size = Pt(12)
    subtitulo.font.color.rgb = RGBColor.from_string(VERDE)

    for nome, tamanho, cor in (
        ("Heading 1", 16, AZUL),
        ("Heading 2", 13, VERDE),
        ("Heading 3", 11.5, AZUL),
    ):
        estilo = documento.styles[nome]
        estilo.font.name = "Calibri"
        estilo.font.size = Pt(tamanho)
        estilo.font.bold = True
        estilo.font.color.rgb = RGBColor.from_string(cor)
        estilo.paragraph_format.keep_with_next = True
        estilo.paragraph_format.space_before = Pt(12)
        estilo.paragraph_format.space_after = Pt(6)


def definir_sombreamento(celula, cor: str) -> None:
    tc_pr = celula._tc.get_or_add_tcPr()
    shd = tc_pr.find(qn("w:shd"))
    if shd is None:
        shd = OxmlElement("w:shd")
        tc_pr.append(shd)
    shd.set(qn("w:fill"), cor)


def definir_margens_celula(celula, superior=90, inferior=90, esquerda=100, direita=100):
    tc = celula._tc
    tc_pr = tc.get_or_add_tcPr()
    tc_mar = tc_pr.first_child_found_in("w:tcMar")
    if tc_mar is None:
        tc_mar = OxmlElement("w:tcMar")
        tc_pr.append(tc_mar)
    for margem, valor in (
        ("top", superior),
        ("bottom", inferior),
        ("start", esquerda),
        ("end", direita),
    ):
        elemento = tc_mar.find(qn(f"w:{margem}"))
        if elemento is None:
            elemento = OxmlElement(f"w:{margem}")
            tc_mar.append(elemento)
        elemento.set(qn("w:w"), str(valor))
        elemento.set(qn("w:type"), "dxa")


def repetir_cabecalho(linha) -> None:
    tr_pr = linha._tr.get_or_add_trPr()
    tbl_header = OxmlElement("w:tblHeader")
    tbl_header.set(qn("w:val"), "true")
    tr_pr.append(tbl_header)


def impedir_quebra_linha(linha) -> None:
    tr_pr = linha._tr.get_or_add_trPr()
    cant_split = OxmlElement("w:cantSplit")
    tr_pr.append(cant_split)


def adicionar_hyperlink(paragrafo, texto: str, url: str, cor=AZUL) -> None:
    parte = paragrafo.part
    r_id = parte.relate_to(
        url,
        "http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink",
        is_external=True,
    )
    hyperlink = OxmlElement("w:hyperlink")
    hyperlink.set(qn("r:id"), r_id)
    run = OxmlElement("w:r")
    r_pr = OxmlElement("w:rPr")
    cor_xml = OxmlElement("w:color")
    cor_xml.set(qn("w:val"), cor)
    sublinhado = OxmlElement("w:u")
    sublinhado.set(qn("w:val"), "single")
    r_pr.append(cor_xml)
    r_pr.append(sublinhado)
    run.append(r_pr)
    texto_xml = OxmlElement("w:t")
    texto_xml.text = texto
    run.append(texto_xml)
    hyperlink.append(run)
    paragrafo._p.append(hyperlink)


def adicionar_numero_pagina(paragrafo) -> None:
    paragrafo.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = paragrafo.add_run("Página ")
    run.font.size = Pt(9)
    inicio = OxmlElement("w:fldChar")
    inicio.set(qn("w:fldCharType"), "begin")
    instrucao = OxmlElement("w:instrText")
    instrucao.set(qn("xml:space"), "preserve")
    instrucao.text = " PAGE "
    fim = OxmlElement("w:fldChar")
    fim.set(qn("w:fldCharType"), "end")
    run._r.append(inicio)
    run._r.append(instrucao)
    run._r.append(fim)


def reiniciar_numero_pagina(secao, inicio: int = 1) -> None:
    sect_pr = secao._sectPr
    pg_num = sect_pr.find(qn("w:pgNumType"))
    if pg_num is None:
        pg_num = OxmlElement("w:pgNumType")
        sect_pr.append(pg_num)
    pg_num.set(qn("w:start"), str(inicio))


def adicionar_texto(documento: Document, texto: str, *, negrito_inicial: str | None = None):
    paragrafo = documento.add_paragraph(style="Normal")
    paragrafo.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    if negrito_inicial and texto.startswith(negrito_inicial):
        paragrafo.add_run(negrito_inicial).bold = True
        paragrafo.add_run(texto[len(negrito_inicial) :])
    else:
        paragrafo.add_run(texto)
    return paragrafo


def adicionar_lista(documento: Document, itens: list[str]) -> None:
    for item in itens:
        paragrafo = documento.add_paragraph(style="List Bullet")
        paragrafo.paragraph_format.space_after = Pt(3)
        paragrafo.add_run(item)


def adicionar_codigo(documento: Document, texto: str) -> None:
    tabela = documento.add_table(rows=1, cols=1)
    tabela.alignment = WD_TABLE_ALIGNMENT.CENTER
    tabela.style = "Table Grid"
    celula = tabela.cell(0, 0)
    definir_sombreamento(celula, "F5F7FA")
    definir_margens_celula(celula, 130, 130, 160, 160)
    paragrafo = celula.paragraphs[0]
    paragrafo.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = paragrafo.add_run(texto)
    run.font.name = "Consolas"
    run.font.size = Pt(9.5)
    documento.add_paragraph()


def adicionar_tabela(
    documento: Document,
    cabecalhos: list[str],
    linhas: list[list[object]],
    *,
    larguras_cm: list[float] | None = None,
    fonte: float = 9,
) -> object:
    tabela = documento.add_table(rows=1, cols=len(cabecalhos))
    tabela.style = "Table Grid"
    tabela.alignment = WD_TABLE_ALIGNMENT.CENTER
    tabela.autofit = False

    cabecalho = tabela.rows[0]
    repetir_cabecalho(cabecalho)
    impedir_quebra_linha(cabecalho)
    for indice, texto in enumerate(cabecalhos):
        celula = cabecalho.cells[indice]
        definir_sombreamento(celula, VERDE)
        definir_margens_celula(celula)
        celula.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
        if larguras_cm:
            celula.width = Cm(larguras_cm[indice])
        paragrafo = celula.paragraphs[0]
        paragrafo.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = paragrafo.add_run(str(texto))
        run.bold = True
        run.font.color.rgb = RGBColor.from_string(BRANCO)
        run.font.size = Pt(fonte)

    for linha in linhas:
        row = tabela.add_row()
        impedir_quebra_linha(row)
        for indice, valor in enumerate(linha):
            celula = row.cells[indice]
            definir_margens_celula(celula)
            celula.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
            if larguras_cm:
                celula.width = Cm(larguras_cm[indice])
            paragrafo = celula.paragraphs[0]
            paragrafo.alignment = (
                WD_ALIGN_PARAGRAPH.CENTER
                if isinstance(valor, (int, float)) or indice == 0 and len(cabecalhos) <= 3
                else WD_ALIGN_PARAGRAPH.LEFT
            )
            run = paragrafo.add_run(str(valor))
            run.font.size = Pt(fonte)

    documento.add_paragraph()
    return tabela


def adicionar_legenda(documento: Document, texto: str, fonte: str) -> None:
    paragrafo = documento.add_paragraph()
    paragrafo.alignment = WD_ALIGN_PARAGRAPH.CENTER
    paragrafo.paragraph_format.keep_with_next = True
    run = paragrafo.add_run(texto)
    run.bold = True
    run.font.size = Pt(9.5)

    paragrafo_fonte = documento.add_paragraph()
    paragrafo_fonte.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run_fonte = paragrafo_fonte.add_run(f"Fonte: {fonte}")
    run_fonte.italic = True
    run_fonte.font.size = Pt(8.5)


def adicionar_figura(documento: Document, caminho: Path, legenda: str, fonte: str) -> None:
    paragrafo = documento.add_paragraph()
    paragrafo.alignment = WD_ALIGN_PARAGRAPH.CENTER
    paragrafo.paragraph_format.keep_with_next = True
    paragrafo.add_run().add_picture(str(caminho), width=Cm(15.6))
    adicionar_legenda(documento, legenda, fonte)


def adicionar_placeholder_snapshot(documento: Document) -> None:
    tabela = documento.add_table(rows=1, cols=1)
    tabela.style = "Table Grid"
    tabela.alignment = WD_TABLE_ALIGNMENT.CENTER
    celula = tabela.cell(0, 0)
    celula.height = Cm(8)
    celula.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
    definir_sombreamento(celula, "F5F7FA")
    paragrafo = celula.paragraphs[0]
    paragrafo.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = paragrafo.add_run(
        "INSERIR AQUI O SNAPSHOT DO GITHUB PROJECT APÓS A ATUALIZAÇÃO FINAL DO BOARD"
    )
    run.bold = True
    run.font.color.rgb = RGBColor.from_string(CINZA_GRAFICO.removeprefix("#"))
    run.font.size = Pt(12)
    documento.add_paragraph()


def adicionar_referencia(documento: Document, prefixo: str, url: str) -> None:
    paragrafo = documento.add_paragraph(style="Normal")
    paragrafo.paragraph_format.left_indent = Cm(0)
    paragrafo.paragraph_format.first_line_indent = Cm(-0.6)
    paragrafo.paragraph_format.left_indent = Cm(0.6)
    paragrafo.add_run(prefixo)
    adicionar_hyperlink(paragrafo, url, url)
    paragrafo.add_run(". Acesso em: 20 ago. 2026.")


def adicionar_titulo_secao(documento: Document, texto: str, *, nova_pagina=False) -> None:
    paragrafo = documento.add_heading(texto, level=1)
    if nova_pagina:
        paragrafo.paragraph_format.page_break_before = True


def rotular_barras(ax, barras, *, formato="{:.0f}", cor=TEXTO, tamanho=9) -> None:
    for barra in barras:
        altura = barra.get_height()
        ax.annotate(
            formato.format(altura),
            (barra.get_x() + barra.get_width() / 2, altura),
            xytext=(0, 4),
            textcoords="offset points",
            ha="center",
            va="bottom",
            fontsize=tamanho,
            color=f"#{cor}",
        )


def preparar_graficos(df: pd.DataFrame, diretorio: Path) -> dict[str, Path]:
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 10,
            "axes.titlesize": 14,
            "axes.titleweight": "bold",
            "axes.labelsize": 10,
            "figure.facecolor": "white",
            "axes.facecolor": "white",
        }
    )
    graficos: dict[str, Path] = {}

    # RQ01
    caminho = diretorio / "rq01_idade.png"
    fig, ax = plt.subplots(figsize=(8.2, 4.6))
    bins = np.arange(0, 22, 2)
    ax.hist(
        df["Idade (anos)"],
        bins=bins,
        color=VERDE_GRAFICO,
        edgecolor="white",
        linewidth=1.2,
    )
    mediana = float(df["Idade (anos)"].median())
    ax.axvline(mediana, color=LARANJA_GRAFICO, linestyle="--", linewidth=2)
    ax.text(
        mediana + 0.25,
        ax.get_ylim()[1] * 0.92,
        f"Mediana: {mediana:.2f} anos".replace(".", ","),
        color=LARANJA_GRAFICO,
        fontweight="bold",
    )
    ax.set_title("Distribuição da idade dos repositórios")
    ax.set_xlabel("Idade (anos)")
    ax.set_ylabel("Número de repositórios")
    ax.set_xticks(np.arange(0, 21, 2))
    ax.set_ylim(bottom=0)
    ax.grid(axis="y", alpha=0.2)
    ax.text(0.99, 0.96, "n = 1.000", transform=ax.transAxes, ha="right", va="top")
    fig.tight_layout()
    fig.savefig(caminho, dpi=220, bbox_inches="tight")
    plt.close(fig)
    graficos["rq01"] = caminho

    # RQ02
    caminho = diretorio / "rq02_prs.png"
    prs = pd.to_numeric(df["PRs aceitas"], errors="coerce")
    faixas = [
        int((prs == 0).sum()),
        int(((prs >= 1) & (prs <= 9)).sum()),
        int(((prs >= 10) & (prs <= 99)).sum()),
        int(((prs >= 100) & (prs <= 999)).sum()),
        int(((prs >= 1_000) & (prs <= 9_999)).sum()),
        int(((prs >= 10_000) & (prs <= 99_999)).sum()),
        int((prs >= 100_000).sum()),
    ]
    rotulos = ["0", "1–9", "10–99", "100–999", "1.000–9.999", "10.000–99.999", "≥100.000"]
    fig, ax = plt.subplots(figsize=(8.6, 4.8))
    barras = ax.bar(rotulos, faixas, color=VERDE_GRAFICO)
    rotular_barras(ax, barras)
    ax.set_title("Repositórios por faixa de PRs mescladas")
    ax.set_xlabel("Quantidade acumulada de PRs mescladas")
    ax.set_ylabel("Número de repositórios")
    ax.set_ylim(0, max(faixas) * 1.2)
    ax.grid(axis="y", alpha=0.2)
    ax.tick_params(axis="x", rotation=22)
    ax.text(
        0.99,
        0.95,
        "Mediana: 768 | Máximo: 103.387",
        transform=ax.transAxes,
        ha="right",
        va="top",
        fontweight="bold",
    )
    fig.tight_layout()
    fig.savefig(caminho, dpi=220, bbox_inches="tight")
    plt.close(fig)
    graficos["rq02"] = caminho

    # RQ03
    caminho = diretorio / "rq03_releases.png"
    releases = pd.to_numeric(df["Total de releases"], errors="coerce")
    faixas = [
        int((releases == 0).sum()),
        int(((releases >= 1) & (releases <= 9)).sum()),
        int(((releases >= 10) & (releases <= 49)).sum()),
        int(((releases >= 50) & (releases <= 99)).sum()),
        int(((releases >= 100) & (releases <= 499)).sum()),
        int(((releases >= 500) & (releases <= 999)).sum()),
        int((releases >= 1_000).sum()),
    ]
    rotulos = ["0", "1–9", "10–49", "50–99", "100–499", "500–999", "≥1.000"]
    fig, ax = plt.subplots(figsize=(8.4, 4.8))
    barras = ax.bar(rotulos, faixas, color=VERDE_GRAFICO)
    rotular_barras(ax, barras)
    ax.set_title("Repositórios por quantidade acumulada de releases")
    ax.set_xlabel("Quantidade acumulada de releases")
    ax.set_ylabel("Número de repositórios")
    ax.set_ylim(0, max(faixas) * 1.25)
    ax.grid(axis="y", alpha=0.2)
    ax.text(
        0.99,
        0.95,
        "Mediana: 41 | 728 com release | Máximo: 6.893",
        transform=ax.transAxes,
        ha="right",
        va="top",
        fontweight="bold",
    )
    fig.tight_layout()
    fig.savefig(caminho, dpi=220, bbox_inches="tight")
    plt.close(fig)
    graficos["rq03"] = caminho

    # RQ04
    caminho = diretorio / "rq04_atualizacao.png"
    dias = pd.to_numeric(df["Dias desde última atualização"], errors="coerce")
    faixas = [
        int((dias <= 1).sum()),
        int(((dias > 1) & (dias <= 7)).sum()),
        int(((dias > 7) & (dias <= 30)).sum()),
        int(((dias > 30) & (dias <= 365)).sum()),
        int((dias > 365).sum()),
    ]
    rotulos = ["Até 1 dia", ">1–7 dias", ">7–30 dias", ">30–365 dias", ">365 dias"]
    fig, ax = plt.subplots(figsize=(8.2, 4.8))
    barras = ax.bar(rotulos, faixas, color=VERDE_GRAFICO)
    for barra, valor in zip(barras, faixas):
        percentual = 100 * valor / len(df)
        ax.annotate(
            f"{valor}\n({percentual:.1f}%)".replace(".", ","),
            (barra.get_x() + barra.get_width() / 2, barra.get_height()),
            xytext=(0, 4),
            textcoords="offset points",
            ha="center",
            va="bottom",
            fontsize=9,
        )
    ax.set_title("Tempo desde o último push")
    ax.set_xlabel("Faixa de recência")
    ax.set_ylabel("Número de repositórios")
    ax.set_ylim(0, max(faixas) * 1.25)
    ax.grid(axis="y", alpha=0.2)
    ax.text(
        0.99,
        0.95,
        "Mediana: 2,00 dias | 72,7% em até 30 dias",
        transform=ax.transAxes,
        ha="right",
        va="top",
        fontweight="bold",
    )
    fig.tight_layout()
    fig.savefig(caminho, dpi=220, bbox_inches="tight")
    plt.close(fig)
    graficos["rq04"] = caminho

    # RQ05
    caminho = diretorio / "rq05_linguagens.png"
    top10 = {
        "TypeScript",
        "Python",
        "JavaScript",
        "Java",
        "C#",
        "PHP",
        "Shell",
        "C++",
        "HCL",
        "Go",
    }
    linguagem = df["Linguagem"].fillna("Não definida")
    contagem_top10 = int(linguagem.isin(top10).sum())
    contagem_indefinida = int((linguagem == "Não definida").sum())
    contagem_outras = len(df) - contagem_top10 - contagem_indefinida
    valores = [contagem_top10, contagem_outras, contagem_indefinida]
    cores = [VERDE_GRAFICO, LARANJA_GRAFICO, CINZA_GRAFICO]
    nomes = ["Top 10 Octoverse", "Outras definidas", "Não definida"]
    fig, ax = plt.subplots(figsize=(8.5, 3.2))
    esquerda = 0
    for valor, cor, nome in zip(valores, cores, nomes):
        ax.barh(["1.000 repositórios"], [valor], left=esquerda, color=cor, label=nome)
        ax.text(
            esquerda + valor / 2,
            0,
            f"{valor}\n{valor / 10:.1f}%".replace(".", ","),
            ha="center",
            va="center",
            color="white",
            fontweight="bold",
            fontsize=10,
        )
        esquerda += valor
    ax.set_xlim(0, 1000)
    ax.set_xlabel("Quantidade de repositórios")
    ax.set_title("Presença das linguagens do Top 10 Octoverse")
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.28), ncol=3, frameon=False)
    ax.grid(axis="x", alpha=0.15)
    fig.tight_layout()
    fig.savefig(caminho, dpi=220, bbox_inches="tight")
    plt.close(fig)
    graficos["rq05"] = caminho

    # RQ06
    caminho = diretorio / "rq06_issues.png"
    percentual = pd.to_numeric(df["% issues fechadas"], errors="coerce")
    validos = percentual.dropna()
    faixas = [
        int(((validos >= limite) & (validos < limite + 10)).sum())
        for limite in range(0, 90, 10)
    ]
    faixas.append(int(((validos >= 90) & (validos <= 100)).sum()))
    faixas.append(int(percentual.isna().sum()))
    rotulos = [
        "0–<10%",
        "10–<20%",
        "20–<30%",
        "30–<40%",
        "40–<50%",
        "50–<60%",
        "60–<70%",
        "70–<80%",
        "80–<90%",
        "90–100%",
        "Não aplicável",
    ]
    cores = [VERDE_GRAFICO] * 10 + [CINZA_GRAFICO]
    fig, ax = plt.subplots(figsize=(9.1, 4.9))
    barras = ax.bar(rotulos, faixas, color=cores)
    rotular_barras(ax, barras, tamanho=8)
    ax.set_title("Distribuição do percentual de issues fechadas")
    ax.set_xlabel("Percentual de fechamento")
    ax.set_ylabel("Número de repositórios")
    ax.tick_params(axis="x", rotation=35)
    ax.set_ylim(0, max(faixas) * 1.2)
    ax.grid(axis="y", alpha=0.2)
    ax.text(
        0.99,
        0.95,
        "Mediana: 87,5% (n = 957) | 43 sem issues",
        transform=ax.transAxes,
        ha="right",
        va="top",
        fontweight="bold",
    )
    fig.tight_layout()
    fig.savefig(caminho, dpi=220, bbox_inches="tight")
    plt.close(fig)
    graficos["rq06"] = caminho

    # RQ07
    caminho = diretorio / "rq07_comparacao.png"
    definidos = df[df["Linguagem"] != "Não definida"].copy()
    definidos["Grupo"] = np.where(
        definidos["Linguagem"].isin(top10),
        "Top 10 Octoverse\n(n=702)",
        "Outras definidas\n(n=211)",
    )
    ordem = ["Top 10 Octoverse\n(n=702)", "Outras definidas\n(n=211)"]
    colunas = [
        ("PRs aceitas", "Mediana de PRs mescladas"),
        ("Total de releases", "Mediana de releases"),
        ("Dias desde última atualização", "Mediana de dias desde o push"),
    ]
    fig, eixos = plt.subplots(1, 3, figsize=(10.2, 4.6))
    for ax, (coluna, titulo) in zip(eixos, colunas):
        medianas = definidos.groupby("Grupo")[coluna].median().reindex(ordem)
        barras = ax.bar(
            [0, 1],
            medianas.values,
            color=[VERDE_GRAFICO, LARANJA_GRAFICO],
            width=0.62,
        )
        for barra, valor in zip(barras, medianas.values):
            if coluna == "Dias desde última atualização":
                rotulo = f"{valor:.2f}".replace(".", ",")
            else:
                rotulo = f"{valor:,.0f}".replace(",", ".")
            ax.annotate(
                rotulo,
                (barra.get_x() + barra.get_width() / 2, valor),
                xytext=(0, 4),
                textcoords="offset points",
                ha="center",
                va="bottom",
                fontweight="bold",
                fontsize=10,
            )
        ax.set_title(titulo, fontsize=10.5, pad=10)
        ax.set_xticks([0, 1], ["Top 10", "Outras"])
        ax.set_ylim(0, max(medianas.values) * 1.18)
        ax.grid(axis="y", alpha=0.2)
    eixos[2].text(
        0.5,
        -0.18,
        "Menor valor = atualização mais recente",
        transform=eixos[2].transAxes,
        ha="center",
        fontsize=8.5,
    )
    fig.suptitle(
        "Indicadores medianos por grupo de linguagens",
        fontsize=14,
        fontweight="bold",
        y=0.99,
    )
    fig.tight_layout(rect=[0, 0, 1, 0.91])
    fig.savefig(caminho, dpi=220, bbox_inches="tight")
    plt.close(fig)
    graficos["rq07"] = caminho

    return graficos


def validar_dados(df: pd.DataFrame) -> None:
    colunas = {
        "Nome",
        "URL",
        "Estrelas",
        "Linguagem",
        "Idade (anos)",
        "PRs aceitas",
        "Total de releases",
        "Dias desde última atualização",
        "Issues abertas",
        "Issues fechadas",
        "% issues fechadas",
    }
    ausentes = colunas.difference(df.columns)
    if ausentes:
        raise RuntimeError(f"CSV sem as colunas esperadas: {sorted(ausentes)}")
    if len(df) != 1_000:
        raise RuntimeError(f"O relatório exige 1.000 registros; o CSV contém {len(df)}.")
    if df["Nome"].nunique() != 1_000 or df["URL"].nunique() != 1_000:
        raise RuntimeError("O CSV não contém 1.000 nomes e URLs únicos.")
    if not df["Estrelas"].is_monotonic_decreasing:
        raise RuntimeError("O CSV não está ordenado por estrelas de forma não crescente.")


def construir_documento(template: Path, saida: Path, df: pd.DataFrame, graficos: dict[str, Path]) -> None:
    documento = Document(template)
    limpar_corpo(documento)
    configurar_estilos(documento)

    # Capa
    p = documento.add_paragraph()
    p.paragraph_format.space_before = Pt(36)
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run("RELATÓRIO DE LABORATÓRIO")
    run.bold = True
    run.font.name = "Calibri"
    run.font.size = Pt(26)
    run.font.color.rgb = RGBColor.from_string("17365D")

    p = documento.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run("Mineração e análise dos 1.000 repositórios mais populares do GitHub")
    run.bold = True
    run.font.size = Pt(15)
    run.font.color.rgb = RGBColor.from_string(VERDE)

    p = documento.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run("Lab01S02")
    run.font.size = Pt(12)
    run.font.color.rgb = RGBColor.from_string(CINZA_GRAFICO.removeprefix("#"))

    documento.add_paragraph()
    capa = documento.add_table(rows=8, cols=2)
    capa.style = "Table Grid"
    capa.alignment = WD_TABLE_ALIGNMENT.CENTER
    capa.autofit = False
    dados_capa = [
        ("Curso", "Engenharia de Software"),
        ("Disciplina", "Laboratório de Experimentação de Software"),
        ("Turno / Período", "Noite / 6º período"),
        ("Professor", "Danilo Maia"),
        ("Laboratório", "Lab01S02 — Paginação e análise de repositórios populares"),
        ("Grupo", "Pedro Henrique Maia Alves e Diogo C. Brunoro"),
        ("Repositório / Project", ""),
        ("Data de entrega", "[INSERIR DATA OFICIAL DE ENTREGA]"),
    ]
    for indice, (rotulo, valor) in enumerate(dados_capa):
        esquerda, direita = capa.rows[indice].cells
        esquerda.width = Cm(4.3)
        direita.width = Cm(12.0)
        definir_sombreamento(esquerda, CINZA_CLARO)
        definir_margens_celula(esquerda, 120, 120, 120, 120)
        definir_margens_celula(direita, 120, 120, 120, 120)
        esquerda.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
        direita.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
        run = esquerda.paragraphs[0].add_run(rotulo)
        run.bold = True
        run.font.size = Pt(10)
        if indice == 6:
            p_link = direita.paragraphs[0]
            adicionar_hyperlink(
                p_link,
                "Repositório",
                "https://github.com/PedroMaiaAlves/lab-experimentacao-software",
            )
            p_link.add_run(" | ")
            adicionar_hyperlink(
                p_link,
                "GitHub Project",
                "https://github.com/users/PedroMaiaAlves/projects/1",
            )
        else:
            run = direita.paragraphs[0].add_run(valor)
            run.font.size = Pt(10)
            if indice == 7:
                run.bold = True
                run.font.color.rgb = RGBColor.from_string(LARANJA_GRAFICO.removeprefix("#"))

    p = documento.add_paragraph()
    p.paragraph_format.space_before = Pt(48)
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.add_run("Belo Horizonte\n2026").font.size = Pt(11)

    # Nova seção para o conteúdo e numeração reiniciada.
    secao_corpo = documento.add_section(WD_SECTION.NEW_PAGE)
    secao_corpo.header.is_linked_to_previous = False
    secao_corpo.footer.is_linked_to_previous = False
    secao_corpo.header_distance = Cm(1.27)
    secao_corpo.footer_distance = Cm(1.27)
    reiniciar_numero_pagina(secao_corpo, 1)
    cabecalho = secao_corpo.header.paragraphs[0]
    cabecalho.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = cabecalho.add_run("Laboratório de Experimentação de Software — Lab01S02")
    run.font.size = Pt(8.5)
    run.font.color.rgb = RGBColor.from_string(CINZA_GRAFICO.removeprefix("#"))
    adicionar_numero_pagina(secao_corpo.footer.paragraphs[0])

    # 1. Introdução
    adicionar_titulo_secao(documento, "1. Introdução")
    adicionar_texto(
        documento,
        "O GitHub é uma plataforma amplamente utilizada para hospedagem, versionamento e colaboração em projetos de software. Seus repositórios apresentam diferentes níveis de popularidade, maturidade, participação da comunidade e atividade de desenvolvimento. A mineração dessas informações permite observar características recorrentes em projetos que alcançaram grande visibilidade e compreender como esses sistemas evoluem, recebem contribuições e administram suas atividades.",
    )
    adicionar_texto(
        documento,
        "Neste laboratório foi realizada uma análise exploratória dos 1.000 repositórios públicos com maior número de estrelas retornados pela API GraphQL do GitHub. O número de estrelas foi adotado como definição operacional de popularidade. Após a coleta, os dados foram transformados em formato tabular, exportados para CSV e analisados de acordo com sete questões de pesquisa propostas pelo professor.",
    )
    adicionar_texto(
        documento,
        "O objetivo geral do trabalho é caracterizar os repositórios populares do GitHub com base em indicadores de idade, pull requests mescladas, releases, recência de atualização, linguagem primária e percentual de issues fechadas. Também foi investigada a relação entre a popularidade da linguagem e os indicadores de contribuição, releases e atualização.",
    )
    adicionar_texto(
        documento,
        "Além das atividades solicitadas, o grupo desenvolveu uma aplicação web em Streamlit. Essa aplicação permite iniciar a mineração por meio de uma interface gráfica, acompanhar o processamento, visualizar os resultados das questões de pesquisa e exportar os dados. A utilização do Streamlit representa a inovação proposta pelo grupo, pois as sete questões de pesquisa foram fornecidas pelo professor.",
    )
    adicionar_texto(
        documento,
        "As hipóteses apresentadas possuem caráter informal e exploratório. Elas orientam a interpretação descritiva dos resultados, sem representar hipóteses confirmatórias ou pré-registradas.",
    )
    adicionar_tabela(
        documento,
        ["Questão de pesquisa", "Hipótese informal"],
        [
            [
                "RQ01 — Sistemas populares são maduros/antigos?",
                "Espera-se que os repositórios populares sejam majoritariamente projetos maduros, apresentando idade mediana superior a cinco anos.",
            ],
            [
                "RQ02 — Sistemas populares recebem muita contribuição externa?",
                "Espera-se que os repositórios populares acumulem um número elevado de pull requests mescladas, com mediana superior a 500, e apresentem uma distribuição assimétrica, na qual poucos projetos concentram valores muito altos.",
            ],
            [
                "RQ03 — Sistemas populares lançam releases com frequência?",
                "Espera-se que a maioria dos repositórios populares possua ao menos uma release publicada no GitHub e acumule múltiplas releases ao longo de sua existência.",
            ],
            [
                "RQ04 — Sistemas populares são atualizados com frequência?",
                "Espera-se que a maioria dos repositórios populares apresente atividade recente, com o último push ocorrido nos últimos 30 dias, embora exista uma parcela de projetos inativos há períodos prolongados.",
            ],
            [
                "RQ05 — Sistemas populares são escritos nas linguagens mais populares?",
                "Espera-se que a maioria dos repositórios populares com linguagem primária definida utilize uma das dez linguagens mais populares do GitHub Octoverse 2025.",
            ],
            [
                "RQ06 — Sistemas populares possuem alto percentual de issues fechadas?",
                "Espera-se que os repositórios populares que possuem issues apresentem percentual mediano de fechamento superior a 80%.",
            ],
            [
                "RQ07 — Linguagens populares recebem mais contribuição, mais releases e mais atualizações?",
                "Espera-se que repositórios cuja linguagem primária pertence ao Top 10 do GitHub Octoverse apresentem maior mediana de pull requests mescladas e releases, além de menor tempo desde o último push, quando comparados aos repositórios escritos em outras linguagens definidas.",
            ],
        ],
        larguras_cm=[5.5, 10.5],
        fonte=8.8,
    )
    adicionar_texto(
        documento,
        "Nas RQ02 e RQ07, a quantidade de pull requests mescladas é utilizada como uma aproximação do volume de contribuições. Entretanto, os campos coletados não permitem identificar se cada contribuição foi realizada por um colaborador externo, por um mantenedor ou por uma conta automatizada. Essa limitação é considerada na discussão dos resultados.",
    )

    # 2. Contexto
    adicionar_titulo_secao(documento, "2. Contexto", nova_pagina=True)
    adicionar_texto(
        documento,
        "O trabalho foi desenvolvido durante as sprints S01 e S02 do Lab01 da disciplina de Laboratório de Experimentação de Software. Na S01 foram implementadas a consulta inicial à API GraphQL, a transformação dos dados e as análises associadas às questões de pesquisa. Também foi criada a primeira versão da interface web em Streamlit.",
    )
    adicionar_texto(
        documento,
        "Na S02, a coleta foi ampliada para os 1.000 repositórios exigidos pelo laboratório. Para isso, foi utilizada paginação baseada em cursores. Também foram implementadas a exportação para CSV, a validação dos dados das sete RQs, a criação das hipóteses informais, a evolução dos gráficos, a atualização da metodologia e a preparação do primeiro snapshot do GitHub Project.",
    )
    adicionar_texto(
        documento,
        "O objeto de estudo é composto pelos 1.000 repositórios públicos retornados pela busca do GitHub em ordem decrescente de estrelas. A consulta empregada foi:",
    )
    adicionar_codigo(documento, "stars:>0 is:public sort:stars-desc")
    adicionar_texto(
        documento,
        "Essa expressão restringe a busca a repositórios públicos e solicita a ordenação decrescente pelo número de estrelas. A escolha das estrelas oferece um critério objetivo de seleção, mas não significa que popularidade represente diretamente qualidade, quantidade de usuários ou utilização em produção.",
    )
    adicionar_texto(
        documento,
        "A conexão GraphQL search retorna no máximo 1.000 resultados. As conexões da API exigem paginação e aceitam no máximo 100 elementos nos argumentos first ou last. O grupo utilizou lotes de até 50 repositórios e percorreu as páginas por meio de endCursor e hasNextPage, seguindo o mecanismo oficial de paginação do GitHub (GITHUB, 2026a; GITHUB, 2026b).",
    )
    adicionar_texto(
        documento,
        "A literatura sobre mineração de repositórios alerta que dados obtidos do GitHub precisam ser interpretados considerando limitações de seleção, representação e utilização dos recursos da plataforma. Nem todos os repositórios utilizam pull requests, releases ou issues da mesma forma, o que pode afetar a interpretação das métricas (KALLIAMVAKOU et al., 2014).",
    )
    adicionar_texto(
        documento,
        "Para a RQ05 e a RQ07, foi adotado o ranking do GitHub Octoverse 2025. As dez linguagens utilizadas como referência foram TypeScript, Python, JavaScript, Java, C#, PHP, Shell, C++, HCL e Go. O ranking representa um retrato temporal da atividade na plataforma.",
    )

    # 3. Metodologia
    adicionar_titulo_secao(documento, "3. Metodologia", nova_pagina=True)
    adicionar_texto(
        documento,
        "Este estudo possui natureza quantitativa, observacional e exploratória. Foram utilizadas informações públicas obtidas diretamente da API GraphQL do GitHub. O processo foi dividido em planejamento, coleta, paginação, transformação, validação, análise, visualização e exportação.",
    )

    documento.add_heading("3.1 Principais desafios", level=2)
    adicionar_texto(
        documento,
        "O primeiro desafio foi coletar os 1.000 repositórios. Uma requisição GraphQL não retorna toda essa quantidade de uma só vez, tornando necessária a implementação de paginação baseada em cursores. O coletor também precisava verificar se existia uma próxima página e se o cursor retornado realmente permitia avançar.",
    )
    adicionar_texto(
        documento,
        "Outro desafio foi garantir a cardinalidade e a unicidade da amostra. Um coletor que simplesmente execute determinado número de requisições pode terminar com menos registros do que o solicitado. Por isso, a implementação do main.py acompanha a quantidade efetivamente coletada, elimina nomes repetidos e somente conclui quando alcança 1.000 repositórios únicos.",
    )
    adicionar_texto(
        documento,
        "A consistência entre formatos também foi relevante. Os dados extraídos precisavam gerar uma lista de nós GraphQL, um CSV normalizado e sete arquivos de resultados sem diferenças de nomes, valores ou quantidade de registros.",
    )
    adicionar_texto(
        documento,
        "A presença de valores ausentes exigiu decisões explícitas. Alguns repositórios não possuem linguagem primária identificada pelo GitHub. Outros não possuem nenhuma issue aberta ou fechada, impossibilitando o cálculo do percentual de fechamento. Esses casos não poderiam ser substituídos arbitrariamente por uma linguagem ou por uma taxa igual a zero.",
    )
    adicionar_texto(
        documento,
        "As distribuições de pull requests, releases e dias desde o último push apresentaram grande assimetria. Poucos projetos concentram valores muito superiores aos demais, fazendo com que a média seja influenciada pelos extremos. Por esse motivo, mediana e quartis foram priorizados.",
    )
    adicionar_texto(
        documento,
        "A RQ07 apresentou um desafio adicional: as linguagens possuem tamanhos de grupos muito diferentes. Algumas aparecem em centenas de repositórios, enquanto outras possuem apenas uma ou duas observações. As medianas de grupos pequenos não oferecem a mesma estabilidade das linguagens mais representadas.",
    )
    adicionar_texto(
        documento,
        "Por fim, a construção do front-end exigiu integrar coleta, transformação, execução das análises, visualização e exportação em um único fluxo interativo.",
    )

    documento.add_heading("3.2 Tomadas de decisão", level=2)
    adicionar_texto(
        documento,
        "A coleta oficial da S02 foi executada pelo main.py, configurado para obter exatamente 1.000 repositórios. Cada consulta solicita até 50 registros e envia, por meio da variável after, o cursor obtido na página anterior.",
    )
    adicionar_texto(
        documento,
        "A query solicita hasNextPage e endCursor dentro de pageInfo. Antes de solicitar uma nova página, o coletor verifica se o GitHub informa resultados adicionais, se o cursor foi retornado e se ainda não havia sido utilizado. Uma página vazia ou o encerramento antes dos 1.000 registros provoca uma falha explícita.",
    )
    adicionar_texto(
        documento,
        "Os nomes completos no formato proprietário/repositório são utilizados como chave de unicidade. Assim, registros repetidos não são adicionados novamente.",
    )
    adicionar_texto(
        documento,
        "A lista de nós extraídos foi armazenada em repositorios_graphql.json. Esse arquivo preserva os campos dos repositórios, mas não representa o envelope integral da resposta GraphQL, pois não contém data, search, pageInfo, cursores ou informações de limite.",
    )
    adicionar_texto(
        documento,
        "Após a coleta, os nós foram transformados em DataFrame e exportados para repositorios_populares.csv. O comando utilizado foi:",
    )
    adicionar_codigo(documento, "python main.py --csv")
    adicionar_lista(
        documento,
        [
            "Representar a ausência de linguagem primária pela categoria Não definida.",
            "Calcular idade pelo número inteiro de dias entre o instante da transformação e createdAt, dividido por 365,25 e arredondado para duas casas.",
            "Calcular recência pela diferença, em dias, entre o instante da transformação e pushedAt.",
            "Calcular o percentual de fechamento somente quando a soma de issues abertas e fechadas for maior que zero.",
            "Manter ausente o percentual dos repositórios que não possuem issues.",
            "Não remover outliers confirmados nos dados recebidos da API.",
            "Priorizar mediana e quartis nas distribuições assimétricas.",
            "Excluir a categoria Não definida da comparação agregada da RQ07.",
            "Utilizar o Octoverse 2025 como referência fixa para as linguagens do Top 10.",
            "Carregar o token pela variável de ambiente GITHUB_TOKEN.",
        ],
    )
    adicionar_texto(
        documento,
        "Os dados oficiais do relatório foram obtidos pelo main.py. O Streamlit foi utilizado como camada interativa e exploratória. Essa separação é importante porque a interface permite escolher outras quantidades e linguagens, podendo gerar amostras diferentes daquela utilizada como snapshot oficial.",
    )

    documento.add_heading("3.3 Etapas e configuração do processo", level=2)
    adicionar_texto(
        documento,
        "O processo foi acompanhado no GitHub Project público denominado Laboratorio de Experimentação - Kanban. O fluxo configurado contém as colunas Backlog, To Do, Doing, In review e Done.",
    )
    adicionar_tabela(
        documento,
        ["Coluna", "Limite de WIP"],
        [["Backlog", 30], ["Doing", 9], ["In review", 5]],
        larguras_cm=[9, 4],
        fonte=9.5,
    )
    adicionar_texto(
        documento,
        "Também foram configurados os campos Priority, Size, Estimate, Start date e Target date. O Project possui visões específicas para backlog, prioridades, itens do time, roadmap e tarefas atribuídas ao usuário atual.",
    )
    adicionar_texto(
        documento,
        "Na S01, Diogo ficou responsável pela consulta automática, RQ01, RQ03, RQ05 e pela primeira versão do Streamlit. Pedro ficou responsável por RQ02, RQ04, RQ06, RQ07 e pelos ajustes de integração.",
    )
    adicionar_tabela(
        documento,
        ["Sprint", "Atividade", "Responsável", "Issue/PR"],
        [
            ["S01", "RQ01 — idade", "Diogo", "Issue #1"],
            ["S01", "RQ02 — pull requests", "Pedro", "Issue #2 / PR #19"],
            ["S01", "RQ03 — releases", "Diogo", "Issue #3"],
            ["S01", "RQ04 — última atualização", "Pedro", "Issue #4 / PR #18"],
            ["S01", "RQ05 — linguagem primária", "Diogo", "Issue #5"],
            ["S01", "RQ06 — issues fechadas", "Pedro", "Issue #6 / PR #17"],
            ["S01", "Consulta automática GraphQL", "Diogo", "Issue #7"],
            ["S01", "Interface web Streamlit", "Diogo", "Issue #9"],
            ["S01", "RQ07 — cruzamento de métricas", "Pedro", "Issue #16 / PR #20"],
            ["S01", "Integração geral", "Pedro", "PR #21"],
        ],
        larguras_cm=[1.4, 7.6, 2.6, 3.8],
        fonte=8.5,
    )
    adicionar_texto(
        documento,
        "Na S02, Diogo realizou a paginação, a coleta dos 1.000 repositórios, a exportação CSV e a evolução dos gráficos. Pedro realizou a validação dos dados, a formulação das hipóteses, a atualização metodológica e a preparação do snapshot.",
    )
    adicionar_tabela(
        documento,
        ["Sprint", "Atividade", "Responsável", "Issue/PR"],
        [
            ["S02", "Paginação da API GraphQL", "Diogo", "Issue #8"],
            ["S02", "Coleta dos 1.000 repositórios", "Diogo", "Issue #10 / PR #27"],
            ["S02", "Exportação para CSV", "Diogo", "Issue #11 / PR #28"],
            ["S02", "Validação geral das RQs", "Pedro", "Issue #12"],
            ["S02", "Hipóteses e validações individuais", "Pedro", "Issues #32–#38"],
            ["S02", "Correção e criação de gráficos", "Diogo", "Issues #29–#30 / PR #31"],
            ["S02", "Criação das hipóteses", "Pedro", "Issue #13"],
            ["S02", "Snapshot do GitHub Project", "Pedro", "Issue #14"],
            ["S02", "Documentação e metodologia", "Pedro/grupo", "Issues #15 e #22–#26"],
        ],
        larguras_cm=[1.4, 7.4, 2.8, 3.8],
        fonte=8.5,
    )
    adicionar_texto(
        documento,
        "As hipóteses individuais foram registradas nos comentários das Issues #32 a #38, fechadas após a validação.",
    )
    adicionar_placeholder_snapshot(documento)
    adicionar_legenda(
        documento,
        "Figura 1 — GitHub Project ao final da S02.",
        "Elaborado pelo grupo, 2026.",
    )

    documento.add_heading("3.4 Ferramentas", level=2)
    adicionar_texto(
        documento,
        "O desenvolvimento foi realizado em Python 3.13.14. Requests 2.34.2 foi utilizada para requisições HTTP à API GraphQL, enquanto python-dotenv 1.2.2 permitiu carregar o token sem incorporá-lo ao código-fonte.",
    )
    adicionar_texto(
        documento,
        "Pandas 3.0.5 foi utilizado na transformação dos nós GraphQL em estrutura tabular, no cálculo das métricas, nos agrupamentos e na exportação. A interface foi construída com Streamlit 1.61.1. Altair 6.2.2 foi empregado nas visualizações interativas.",
    )
    adicionar_texto(
        documento,
        "Git e GitHub foram utilizados no controle de versão. Issues, pull requests e GitHub Projects registraram tarefas, responsáveis e andamento do trabalho.",
    )
    adicionar_lista(
        documento,
        [
            "github_collector/schema.py: definição da query GraphQL.",
            "github_collector/client.py: comunicação utilizada pelo Streamlit.",
            "utils/dataframe.py: transformação dos nós para a tabela analítica.",
            "analysis: módulos independentes de RQ01–RQ07.",
            "main.py: coleta oficial em lote, exportação e análises.",
            "app.py: camada interativa de apresentação.",
        ],
    )
    adicionar_texto(
        documento,
        "As versões foram obtidas do ambiente virtual. Como ainda não existe arquivo de dependências versionado, recomenda-se criar um requirements.txt para melhorar a reprodução.",
    )

    documento.add_heading("3.5 Tabela de métricas", level=2)
    adicionar_tabela(
        documento,
        ["RQ", "Métrica", "Definição operacional", "Unidade", "Fonte"],
        [
            ["RQ01", "Idade", "Diferença entre transformação e createdAt, dividida por 365,25", "Anos", "GraphQL"],
            ["RQ02", "PRs mescladas", "pullRequests(states: MERGED).totalCount", "Quantidade", "GraphQL"],
            ["RQ03", "Releases", "releases.totalCount", "Quantidade acumulada", "GraphQL"],
            ["RQ04", "Recência", "Diferença entre transformação e pushedAt", "Dias", "GraphQL"],
            ["RQ05", "Linguagem popular", "Pertencimento de primaryLanguage ao Top 10 Octoverse 2025", "Categoria / %", "GraphQL e Octoverse"],
            ["RQ06", "Issues fechadas", "100 × fechadas / (abertas + fechadas)", "Percentual", "GraphQL"],
            ["RQ07", "Linguagem versus métricas", "Comparação das medianas de RQ02–RQ04 entre Top 10 e demais", "Medianas por grupo", "Dados derivados"],
        ],
        larguras_cm=[1.1, 2.7, 6.4, 2.3, 3.2],
        fonte=8,
    )
    adicionar_texto(
        documento,
        "A RQ03 utiliza o termo frequência, mas a implementação mede a quantidade acumulada de releases. Uma frequência exigiria normalização pela idade ou intervalos entre releases. Da mesma maneira, a RQ04 mede recência do último push, não a frequência histórica.",
    )

    documento.add_heading("3.6 Inovação proposta pelo grupo", level=2)
    adicionar_texto(
        documento,
        "As sete questões de pesquisa foram sugeridas pelo professor e não constituem contribuição adicional. A inovação proposta foi uma aplicação web com Streamlit para integrar mineração, processamento, análise, visualização e exportação em um único ambiente.",
    )
    adicionar_texto(
        documento,
        "O Streamlit é um framework Python para construção de aplicações dinâmicas de dados. Sua utilização permitiu transformar os scripts em uma interface navegável, reduzindo a necessidade de interação direta com o terminal.",
    )
    adicionar_texto(
        documento,
        "A aplicação permite informar o token por campo protegido ou variável de ambiente, escolher uma linguagem opcional, solicitar entre 1 e 1.000 repositórios e iniciar a consulta. Uma barra de progresso informa o andamento e mensagens específicas tratam erros HTTP, GraphQL e de conexão.",
    )
    adicionar_texto(
        documento,
        "Depois da coleta, os dados são transformados e as sete análises executadas automaticamente. A interface apresenta indicadores, uma aba por RQ, distribuições, rankings, tabelas, URLs clicáveis, cruzamentos por linguagem e download de CSV enriquecido.",
    )
    adicionar_texto(
        documento,
        "Essa inovação possui caráter de engenharia, transparência e comunicação. Para consistência, o snapshot oficial foi produzido pelo main.py; o Streamlit foi tratado como ferramenta exploratória, pois aceita filtros e quantidades diferentes.",
    )
    adicionar_texto(
        documento,
        "A aplicação representa uma primeira versão. Sua quantidade padrão é 100; o coletor do app.py não possui as mesmas garantias de cardinalidade, unicidade e avanço de cursor do main.py, e sua query não inclui explicitamente is:public. Uma consulta pode sobrescrever o CSV, o JSON normalizado e os resultados das RQs. A interface também anuncia um filtro mínimo de três repositórios por linguagem que o módulo ainda não aplica, e a visualização da RQ07 precisa diferenciar o Top 10 das demais linguagens.",
    )

    # 4. Resultados
    adicionar_titulo_secao(documento, "4. Resultados", nova_pagina=True)
    documento.add_heading("4.1 Coleta e validação dos dados", level=2)
    adicionar_texto(
        documento,
        "O snapshot validado foi gerado em 20 de agosto de 2026. A transformação ocorreu aproximadamente às 09h49 no horário de Brasília, valor inferido dos artefatos porque o horário exato ainda não é armazenado como metadado.",
    )
    adicionar_texto(
        documento,
        "A coleta produziu exatamente 1.000 repositórios, com 1.000 nomes e 1.000 URLs únicas. A lista de nós GraphQL e o CSV contêm os mesmos projetos e na mesma ordem.",
    )
    adicionar_texto(
        documento,
        "Os repositórios estão organizados pelo número de estrelas de forma não crescente. No instante da coleta, o maior valor foi 541.471 estrelas e o menor foi 32.950.",
    )
    adicionar_texto(
        documento,
        "O CSV possui 1.000 linhas e 11 colunas: Nome, URL, Estrelas, Linguagem, Idade em anos, PRs aceitas, Total de releases, Dias desde a última atualização, Issues abertas, Issues fechadas e Percentual de issues fechadas.",
    )
    adicionar_texto(
        documento,
        "Os campos diretamente coletados foram comparados entre JSON e CSV. Nenhuma divergência foi encontrada, e os sete arquivos de resultados coincidiram com o recálculo realizado a partir do CSV. Esse snapshot foi validado localmente e deve ser versionado antes da entrega para completar sua rastreabilidade.",
    )
    adicionar_texto(
        documento,
        "Foram encontrados 87 repositórios sem linguagem primária, representados por Não definida, e 43 sem issues abertas ou fechadas. Nesses casos, o percentual de fechamento foi mantido ausente. Não foram observados valores negativos, contagens fracionárias, percentuais fora de 0% a 100% ou duplicações.",
    )
    adicionar_texto(
        documento,
        "Os outliers identificados estavam presentes nos dados GraphQL e foram mantidos. Sua remoção reduziria artificialmente a diversidade da amostra.",
    )
    adicionar_texto(
        documento,
        "Durante a validação foi identificado um artefato inconsistente denominado repositorios_populares.json, com somente 100 registros e valores NaN. Ele foi excluído da análise da S02. Os artefatos canônicos são repositorios_graphql.json, repositorios_populares.csv e os sete arquivos de RQ.",
    )

    documento.add_heading("4.2 Visualizações e resultados por RQ", level=2)

    documento.add_heading("4.2.1 RQ01 — Sistemas populares são maduros/antigos?", level=3)
    adicionar_texto(
        documento,
        "A idade mediana foi de 7,74 anos e a média foi de 7,66 anos. O mínimo foi 0,02 ano e o máximo 18,36 anos. Dos 1.000 projetos, 139 tinham menos de dois anos, 185 entre dois e menos de cinco, 331 entre cinco e menos de dez e 345 tinham dez anos ou mais.",
    )
    adicionar_texto(
        documento,
        "Assim, 676 repositórios, correspondentes a 67,6% da amostra, possuíam pelo menos cinco anos. Nenhum valor foi classificado como outlier pelo critério de 1,5 vezes a amplitude interquartil.",
    )
    adicionar_figura(
        documento,
        graficos["rq01"],
        "Figura 2 — Distribuição da idade dos repositórios.",
        "Elaborado pelo grupo com dados da API GraphQL do GitHub, 2026.",
    )

    documento.add_heading("4.2.2 RQ02 — Sistemas populares recebem muita contribuição externa?", level=3)
    adicionar_texto(
        documento,
        "A mediana foi de 768 pull requests mescladas e a média foi de 4.240,84. O primeiro quartil foi 175, o terceiro 3.423,5 e o máximo 103.387. Vinte repositórios apresentaram zero PRs mescladas.",
    )
    adicionar_texto(
        documento,
        "Foram identificados 124 outliers superiores. A diferença entre média e mediana demonstra forte assimetria, com poucos projetos concentrando uma quantidade muito elevada.",
    )
    adicionar_tabela(
        documento,
        ["Repositório", "PRs mescladas"],
        [
            ["firstcontributions/first-contributions", "103.387"],
            ["llvm/llvm-project", "97.254"],
            ["elastic/elasticsearch", "95.619"],
        ],
        larguras_cm=[11, 4],
        fonte=9,
    )
    adicionar_figura(
        documento,
        graficos["rq02"],
        "Figura 3 — Distribuição dos repositórios por faixa de pull requests mescladas.",
        "Elaborado pelo grupo com dados da API GraphQL do GitHub, 2026.",
    )

    documento.add_heading("4.2.3 RQ03 — Sistemas populares lançam releases com frequência?", level=3)
    adicionar_texto(
        documento,
        "A mediana foi de 41 releases e a média foi de 158,23. O primeiro quartil foi zero, o terceiro 153 e o máximo 6.893. Dos 1.000 projetos, 728 possuíam ao menos uma release, representando 72,8% da amostra; 272 apresentaram zero.",
    )
    adicionar_texto(
        documento,
        "Foram identificados 90 outliers superiores, confirmando que poucos projetos acumulam números muito acima da maior parte da amostra.",
    )
    adicionar_tabela(
        documento,
        ["Repositório", "Releases"],
        [
            ["ggml-org/llama.cpp", "6.893"],
            ["gradio-app/gradio", "5.090"],
            ["vercel/next.js", "3.810"],
        ],
        larguras_cm=[11, 4],
        fonte=9,
    )
    adicionar_figura(
        documento,
        graficos["rq03"],
        "Figura 4 — Distribuição dos repositórios por quantidade acumulada de releases.",
        "Elaborado pelo grupo com dados da API GraphQL do GitHub, 2026.",
    )

    documento.add_heading("4.2.4 RQ04 — Sistemas populares são atualizados com frequência?", level=3)
    adicionar_texto(
        documento,
        "A mediana do tempo desde o último push foi de aproximadamente 2,00 dias. A média foi de 114,05 dias e o máximo chegou a 2.452,35 dias.",
    )
    adicionar_tabela(
        documento,
        ["Recência", "Repositórios"],
        [
            ["Até 1 dia", 439],
            ["Mais de 1 e até 7 dias", 165],
            ["Mais de 7 e até 30 dias", 123],
            ["Mais de 30 e até 365 dias", 158],
            ["Mais de 365 dias", 115],
        ],
        larguras_cm=[11, 4],
        fonte=9,
    )
    adicionar_texto(
        documento,
        "Portanto, 727 repositórios, ou 72,7%, receberam um push nos 30 dias anteriores à transformação. Ao mesmo tempo, 11,5% estavam há mais de um ano sem push. Foram identificados 197 outliers superiores.",
    )
    adicionar_texto(
        documento,
        "Um valor igual a zero foi produzido porque o pushedAt retornado pelo GitHub estava aproximadamente 17 segundos à frente do relógio utilizado. O código limitou o resultado mínimo a zero. Quando pushedAt está ausente, a transformação utiliza createdAt como alternativa; esse fallback não foi acionado nos 1.000 registros desta coleta.",
    )
    adicionar_figura(
        documento,
        graficos["rq04"],
        "Figura 5 — Distribuição do tempo desde o último push.",
        "Elaborado pelo grupo com dados da API GraphQL do GitHub, 2026.",
    )

    documento.add_heading("4.2.5 RQ05 — Sistemas populares são escritos nas linguagens mais populares?", level=3)
    adicionar_texto(
        documento,
        "Foram identificadas 43 linguagens efetivamente definidas. O resultado apresenta 44 categorias porque inclui Não definida.",
    )
    adicionar_tabela(
        documento,
        ["Linguagem", "Repositórios"],
        [
            ["Python", 227],
            ["TypeScript", 173],
            ["JavaScript", 111],
            ["Não definida", 87],
            ["Go", 77],
            ["Rust", 58],
            ["C++", 41],
            ["Java", 41],
        ],
        larguras_cm=[10, 4],
        fonte=9,
    )
    adicionar_texto(
        documento,
        "Python, TypeScript e JavaScript concentram 511 repositórios. Ao todo, 702 projetos utilizam uma linguagem do Top 10, correspondendo a 70,2% da amostra. Considerando somente os 913 com linguagem definida, a proporção é 76,9%. Doze linguagens aparecem em somente um repositório.",
    )
    adicionar_figura(
        documento,
        graficos["rq05"],
        "Figura 6 — Participação das linguagens do Top 10 do GitHub Octoverse.",
        "Elaborado pelo grupo com dados da API GraphQL e do GitHub Octoverse 2025.",
    )

    documento.add_heading("4.2.6 RQ06 — Sistemas populares possuem alto percentual de issues fechadas?", level=3)
    adicionar_texto(
        documento,
        "O percentual foi calculado para 957 repositórios; nos 43 restantes não existiam issues abertas ou fechadas. Entre os válidos, a mediana foi 87,5%, a média 80,25%, o primeiro quartil 70,4%, o terceiro 96,8%, o mínimo 7,7% e o máximo 100%.",
    )
    adicionar_texto(
        documento,
        "Dos 957 repositórios com issues, 618, equivalentes a 64,6%, apresentaram pelo menos 80% de fechamento. Em contrapartida, 108 projetos, ou 11,3%, possuíam percentual abaixo de 50%. Foram identificados 38 outliers inferiores.",
    )
    adicionar_figura(
        documento,
        graficos["rq06"],
        "Figura 7 — Distribuição do percentual de issues fechadas.",
        "Elaborado pelo grupo com dados da API GraphQL do GitHub, 2026.",
    )

    documento.add_heading("4.2.7 RQ07 — Linguagens populares recebem mais contribuição, releases e atualizações?", level=3)
    adicionar_texto(
        documento,
        "Os 913 repositórios com linguagem definida foram divididos entre linguagens do Top 10 e outras linguagens. Os 87 classificados como Não definida foram excluídos. Essa comparação agregada foi recalculada para o relatório a partir do CSV; o JSON atual da RQ07 armazena as medianas separadas por linguagem e a marcação de pertencimento ao Top 10.",
    )
    adicionar_tabela(
        documento,
        ["Grupo", "N", "Mediana de PRs", "Mediana de releases", "Mediana de dias"],
        [
            ["Linguagens Top 10", 702, "1.000", "64", "1,05"],
            ["Outras linguagens definidas", 211, "670", "31", "3,67"],
        ],
        larguras_cm=[5.2, 1.2, 3.1, 3.4, 3.0],
        fonte=8.5,
    )
    adicionar_texto(
        documento,
        "Os projetos associados ao Top 10 apresentaram maior mediana de pull requests e releases e menor número de dias desde o último push, indicando maior recência.",
    )
    adicionar_texto(
        documento,
        "A comparação individual exige cautela: das 44 categorias apresentadas, 24 possuem menos de cinco repositórios, 19 possuem no máximo dois e 12 são representadas por um único projeto.",
    )
    adicionar_figura(
        documento,
        graficos["rq07"],
        "Figura 8 — Indicadores medianos por grupo de linguagens.",
        "Elaborado pelo grupo com dados da API GraphQL e do GitHub Octoverse 2025.",
    )

    documento.add_heading("4.3 Discussão", level=2)
    discussoes = [
        (
            "4.3.1 RQ01",
            "O resultado foi compatível com a expectativa informal de que repositórios populares tendem a ser maduros. A mediana de 7,74 anos ultrapassou cinco anos, e 67,6% da amostra possuía cinco anos ou mais. Entretanto, projetos antigos tiveram mais tempo para acumular estrelas; não se pode concluir que maturidade seja consequência da popularidade.",
        ),
        (
            "4.3.2 RQ02",
            "A mediana de 768 PRs ultrapassou o limiar operacional da expectativa informal. Os 124 outliers e a diferença entre média e mediana são compatíveis com a assimetria esperada. A comparação vale somente para PRs mescladas; a origem externa não pode ser confirmada.",
        ),
        (
            "4.3.3 RQ03",
            "O resultado foi compatível com a expectativa quanto à presença e quantidade acumulada: 72,8% possuíam release e a mediana foi 41. O total não mede frequência temporal; projetos antigos tiveram mais tempo para acumular versões e alguns utilizam outros canais.",
        ),
        (
            "4.3.4 RQ04",
            "O resultado foi compatível com a expectativa quanto à recência. Um total de 72,7% recebeu push nos 30 dias anteriores e a mediana foi dois dias. A métrica não representa frequência histórica nem distingue atualizações manuais de automáticas.",
        ),
        (
            "4.3.5 RQ05",
            "O resultado foi compatível com a expectativa: linguagens Top 10 estavam em 70,2% da amostra e 76,9% dos projetos com linguagem definida. O resultado depende do ranking e de sua data, e a linguagem primária simplifica projetos multilíngues.",
        ),
        (
            "4.3.6 RQ06",
            "A mediana de 87,5% ultrapassou o limiar de 80%. Entre os projetos com issues, 64,6% possuíam pelo menos 80% de fechamento. A taxa não informa tempo, complexidade ou qualidade da solução e pode omitir rastreadores externos.",
        ),
        (
            "4.3.7 RQ07",
            "O resultado foi compatível com a expectativa informal: o grupo Top 10 apresentou mais PRs, mais releases e menor tempo desde o push. A associação não é causal; idade, domínio, comunidade, governança e automação podem influenciar os resultados.",
        ),
    ]
    for titulo, texto in discussoes:
        documento.add_heading(titulo, level=3)
        adicionar_texto(documento, texto)

    adicionar_tabela(
        documento,
        ["Hipótese", "Avaliação"],
        [
            ["H01 — idade mediana superior a cinco anos", "Resultado compatível com a expectativa"],
            ["H02 — elevado número de contribuições", "Compatível para PRs mescladas; origem externa não identificada"],
            ["H03 — maioria com releases", "Compatível para presença e quantidade; frequência não medida"],
            ["H04 — atualização nos últimos 30 dias", "Compatível para recência; frequência histórica não medida"],
            ["H05 — maioria nas linguagens Top 10", "Resultado compatível com a expectativa"],
            ["H06 — mediana de fechamento superior a 80%", "Compatível entre os projetos com issues"],
            ["H07 — indicadores superiores no Top 10", "Compatível descritivamente, sem evidência causal"],
        ],
        larguras_cm=[7.5, 8.5],
        fonte=8.5,
    )

    documento.add_heading("4.3.8 Ameaças à validade", level=3)
    adicionar_texto(
        documento,
        "Validade de construto. Estrelas são aproximação de popularidade. PRs mescladas não identificam contribuição externa. Releases acumuladas não medem frequência, dias desde o push medem recência, e linguagem primária não representa toda a composição de projetos multilíngues.",
        negrito_inicial="Validade de construto.",
    )
    adicionar_texto(
        documento,
        "Validade interna. O estudo é observacional e não controla idade, domínio, tamanho da equipe ou governança. As relações encontradas não devem ser interpretadas como causais.",
        negrito_inicial="Validade interna.",
    )
    adicionar_texto(
        documento,
        "Validade externa. A amostra contém somente os 1.000 repositórios públicos com mais estrelas retornados pela busca. Os resultados não são automaticamente generalizáveis para repositórios menos populares ou privados.",
        negrito_inicial="Validade externa.",
    )
    adicionar_texto(
        documento,
        "Validade de conclusão. Foram utilizadas estatísticas descritivas, sem testes de significância ou modelos de controle. Grupos pequenos tornam algumas medianas por linguagem instáveis.",
        negrito_inicial="Validade de conclusão.",
    )
    adicionar_texto(
        documento,
        "Validade temporal. Estrelas, PRs, releases, issues e atualizações mudam continuamente. A paginação ocorre em chamadas separadas, durante as quais a ordenação pode variar.",
        negrito_inicial="Validade temporal.",
    )
    adicionar_texto(
        documento,
        "Confiabilidade e reprodutibilidade. O instante e os parâmetros não são armazenados como metadados e não existe arquivo de dependências versionado. A interface e o lote utilizam coletores diferentes.",
        negrito_inicial="Confiabilidade e reprodutibilidade.",
    )
    adicionar_texto(
        documento,
        "Limitações da inovação. O Streamlit não carrega automaticamente o snapshot persistido. Uma nova busca pode sobrescrever arquivos, a quantidade padrão é 100 e a visualização da RQ07 ainda requer correções.",
        negrito_inicial="Limitações da inovação.",
    )

    # 5. Conclusão
    adicionar_titulo_secao(documento, "5. Conclusão", nova_pagina=True)
    adicionar_texto(
        documento,
        "Este trabalho apresentou uma análise exploratória dos 1.000 repositórios públicos com maior número de estrelas retornados pela API GraphQL do GitHub. A paginação permitiu atingir a quantidade exigida, enquanto a validação confirmou 1.000 nomes e URLs únicos.",
    )
    adicionar_texto(
        documento,
        "Os dados armazenados na lista de nós GraphQL, no CSV e nos arquivos das sete RQs mostraram-se consistentes. Não foram encontradas divergências nos campos diretamente coletados, duplicações ou valores fora de seus domínios esperados.",
    )
    adicionar_texto(
        documento,
        "Os projetos analisados são majoritariamente maduros e apresentam atividade recente. A idade mediana foi 7,74 anos, e 72,7% receberam um push nos 30 dias anteriores.",
    )
    adicionar_texto(
        documento,
        "As distribuições de PRs e releases apresentaram forte assimetria. A mediana foi 768 PRs e 41 releases, mas poucos projetos concentraram valores muito elevados. Por isso, as medianas se mostraram mais representativas que as médias.",
    )
    adicionar_texto(
        documento,
        "As linguagens Top 10 do Octoverse estavam em 70,2% da amostra e 76,9% dos projetos com linguagem definida. Entre os projetos com issues, a mediana de fechamento foi 87,5%.",
    )
    adicionar_texto(
        documento,
        "A RQ07 mostrou que projetos associados ao Top 10 possuíam, descritivamente, mais PRs, mais releases e maior recência. Essa associação não permite concluir causalidade.",
    )
    adicionar_texto(
        documento,
        "Os resultados observados foram compatíveis com as expectativas informais formuladas para as RQs. Essa comparação é exclusivamente exploratória, pois as hipóteses não foram pré-registradas e foram redigidas após uma inspeção preliminar da coleta. A análise não identifica a origem externa, não mede diretamente a frequência de releases e utiliza o último push como aproximação de atualização.",
    )
    adicionar_texto(
        documento,
        "A principal inovação foi a aplicação em Streamlit, que integra parâmetros de mineração, acompanhamento, análises, indicadores, gráficos, inspeção tabular e download do CSV. O laboratório passa a possuir uma camada interativa de comunicação e exploração.",
    )
    adicionar_texto(documento, "Como trabalhos futuros, recomenda-se:")
    adicionar_lista(
        documento,
        [
            "Unificar os coletores utilizados pelo main.py e pelo app.py.",
            "Proteger o snapshot oficial contra sobrescrita por consultas exploratórias.",
            "Permitir que o Streamlit carregue dados já coletados.",
            "Armazenar data, horário, query, quantidade, cursores e limite da API como metadados.",
            "Versionar dependências em requirements.txt.",
            "Identificar se os autores das PRs são externos.",
            "Normalizar releases e contribuições pela idade.",
            "Analisar múltiplos snapshots em diferentes datas.",
            "Aplicar testes estatísticos e intervalos de confiança.",
            "Corrigir e ampliar a comparação visual da RQ07.",
        ],
    )

    # 6. Referências
    adicionar_titulo_secao(documento, "6. Referências", nova_pagina=True)
    adicionar_referencia(
        documento,
        "ALVES, Pedro Henrique Maia; BRUNORO, Diogo C. Lab-experimentacao-software. GitHub, 2026. Disponível em: ",
        "https://github.com/PedroMaiaAlves/lab-experimentacao-software",
    )
    adicionar_referencia(
        documento,
        "GITHUB. GraphQL API documentation. 2026a. Disponível em: ",
        "https://docs.github.com/en/graphql",
    )
    adicionar_referencia(
        documento,
        "GITHUB. Using pagination in the GraphQL API. 2026b. Disponível em: ",
        "https://docs.github.com/en/graphql/guides/using-pagination-in-the-graphql-api",
    )
    adicionar_referencia(
        documento,
        "GITHUB. Queries: search. 2026c. Disponível em: ",
        "https://docs.github.com/en/graphql/reference/queries#search",
    )
    adicionar_referencia(
        documento,
        "GITHUB. Octoverse: a new developer joins GitHub every second as AI leads TypeScript to #1. Publicado em 28 out. 2025; atualizado em 28 fev. 2026. Disponível em: ",
        "https://github.blog/news-insights/octoverse/octoverse-a-new-developer-joins-github-every-second-as-ai-leads-typescript-to-1/",
    )
    adicionar_referencia(
        documento,
        "KALLIAMVAKOU, E.; GOUSIOS, G.; BLINCOE, K.; SINGER, L.; GERMAN, D. M.; DAMIAN, D. The promises and perils of mining GitHub. In: Proceedings of the 11th Working Conference on Mining Software Repositories. ACM, 2014. p. 92–101. DOI: ",
        "https://doi.org/10.1145/2597073.2597074",
    )
    adicionar_referencia(
        documento,
        "PANDAS. Pandas documentation. Disponível em: ",
        "https://pandas.pydata.org/docs/",
    )
    adicionar_referencia(
        documento,
        "PYTHON SOFTWARE FOUNDATION. Python documentation. Disponível em: ",
        "https://docs.python.org/3/",
    )
    adicionar_referencia(
        documento,
        "REQUESTS. Requests: HTTP for Humans. Disponível em: ",
        "https://requests.readthedocs.io/en/latest/",
    )
    adicionar_referencia(
        documento,
        "STREAMLIT. Streamlit documentation. Disponível em: ",
        "https://docs.streamlit.io/",
    )
    adicionar_referencia(
        documento,
        "VEGA-ALTAIR. Declarative visualization in Python. Disponível em: ",
        "https://altair-viz.github.io/",
    )

    # Metadados
    propriedades = documento.core_properties
    propriedades.title = "Lab01S02 — Mineração e análise dos 1.000 repositórios mais populares do GitHub"
    propriedades.subject = "Relatório de Laboratório de Experimentação de Software"
    propriedades.author = "Pedro Henrique Maia Alves; Diogo C. Brunoro"
    propriedades.keywords = "GitHub, GraphQL, Streamlit, mineração de repositórios, Lab01S02"

    saida.parent.mkdir(parents=True, exist_ok=True)
    documento.save(saida)


def criar_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--template", type=Path, default=TEMPLATE_PADRAO)
    parser.add_argument("--csv", type=Path, default=CSV_PADRAO)
    parser.add_argument("--saida", type=Path, default=SAIDA_PADRAO)
    return parser


def main() -> None:
    argumentos = criar_parser().parse_args()
    if not argumentos.template.exists():
        raise SystemExit(f"Template não encontrado: {argumentos.template}")
    if not argumentos.csv.exists():
        raise SystemExit(f"CSV não encontrado: {argumentos.csv}")

    df = pd.read_csv(argumentos.csv)
    validar_dados(df)
    with tempfile.TemporaryDirectory(prefix="lab01s02_figuras_") as pasta:
        graficos = preparar_graficos(df, Path(pasta))
        construir_documento(argumentos.template, argumentos.saida, df, graficos)
    print(f"Relatório gerado em: {argumentos.saida.resolve()}")


if __name__ == "__main__":
    main()
