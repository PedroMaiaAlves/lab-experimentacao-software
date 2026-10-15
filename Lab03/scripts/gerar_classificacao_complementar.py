"""Prepara sugestões de tipo para revisão humana, sem alterar classificações finais."""
import argparse
import csv
import json
from pathlib import Path

def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--entrada", required=True, help="JSON com full_name, description, topics e homepage")
    parser.add_argument("--saida", default="cache/classificacao_sugestoes", help="Pasta nova para sugestões não revisadas")
    args = parser.parse_args(argv)
    out_dir = Path(args.saida).resolve()
    finais = Path(__file__).resolve().parents[1] / "data/classificacao_complementar"
    if out_dir == finais or finais in out_dir.parents:
        raise ValueError("as sugestões não podem ser gravadas na pasta de classificações finais")
    if out_dir.exists():
        raise FileExistsError("a pasta de sugestões já existe; use uma pasta nova para preservar revisões")
    items = json.loads(Path(args.entrada).read_text(encoding="utf-8"))
    if len(items) != 240 or len({item["full_name"] for item in items}) != 240:
        raise ValueError("a entrada deve conter exatamente 240 projetos distintos")

    OVERRIDES = {
        "apache/struts": ("biblioteca/framework", "Framework MVC corporativo para desenvolvimento de aplicacoes web Java."),
        "Badgerati/Pode": ("biblioteca/framework", "Framework web multiplataforma para PowerShell para APIs e microsservicos."),
        "VisActor/VChart": ("biblioteca/framework", "Biblioteca de visualizacao de dados e graficos para web."),
        "boxdot/gurk-rs": ("ferramenta CLI", "Cliente de terminal para o Signal Messenger."),
        "cheeaun/phanpy": ("aplicação/serviço", "Cliente web e aplicacao para a rede Mastodon."),
        "dtcooper/raspotify": ("aplicação/serviço", "Daemon do Spotify Connect para sistemas Debian/Raspberry Pi."),
        "edde746/plezy": ("aplicação/serviço", "Aplicativo cliente multiplataforma para o Plex."),
        "AltanS/collie": ("aplicação/serviço", "Cliente PWA e mobile para gestao de agentes."),
        "TableProApp/TablePro": ("aplicação/serviço", "Aplicativo desktop para gerenciamento de tabelas e bancos de dados."),
        "Arthur-Ficial/apfel": ("ferramenta CLI", "Ferramenta CLI e servidor local para interacao com IA."),
        "CodeWithCJ/SparkyFitness": ("aplicação/serviço", "Aplicativo para rastreamento de saude, exercicios e nutricao."),
        "Dataojitori/nocturne_memory": ("aplicação/serviço", "Servidor de memoria de longo prazo para agentes MCP."),
        "EpicenterHQ/epicenter": ("biblioteca/framework", "Framework para criacao de aplicacoes descentralizadas e local-first."),
        "typetools/checker-framework": ("biblioteca/framework", "Framework de verificacao plugavel de tipos e analise estatica para Java."),
        "dubzzz/fast-check": ("biblioteca/framework", "Framework de property-based testing para JavaScript e TypeScript."),
        "guohuiyuan/go-music-dl": ("ferramenta CLI", "Ferramenta CLI para busca e download de musicas via terminal."),
        "googleapis/go-genai": ("biblioteca/framework", "SDK oficial em Go para a API Gemini do Google Gen AI."),
        "byJoey/ech-wk": ("aplicação/serviço", "Worker e proxy reverso para suporte a ECH."),
        "rhysd/actionlint": ("ferramenta CLI", "Linter estatico de linha de comando para workflows do GitHub Actions."),
        "simonw/sqlite-utils": ("ferramenta CLI", "Utilitario CLI e biblioteca Python para manipulacao de bancos SQLite."),
        "tafia/calamine": ("biblioteca/framework", "Biblioteca em Rust para leitura de planilhas Excel (XLSX, XLS)."),
        "utkuozdemir/pv-migrate": ("ferramenta CLI", "Ferramenta CLI para migracao de Persistent Volumes no Kubernetes."),
        "XuehaiPan/nvitop": ("ferramenta CLI", "Monitor interativo em linha de comando (TUI) para GPUs NVIDIA."),
        "privatenumber/pkgroll": ("ferramenta CLI", "Empacotador e bundler de linha de comando para pacotes JavaScript."),
        "scverse/gget": ("ferramenta CLI", "Ferramenta CLI e pacote para consulta de dados genomicos."),
        "sysadminsmedia/homebox": ("aplicação/serviço", "Sistema web auto-hospedado de gerenciamento de inventario domestico."),
        "TomBursch/kitchenowl": ("aplicação/serviço", "Aplicativo web auto-hospedado para gestao de receitas e compras."),
        "mozilla/pontoon": ("aplicação/serviço", "Sistema web de localizacao e gestao de traducoes da Mozilla."),
        "Swetrix/swetrix": ("aplicação/serviço", "Plataforma web auto-hospedada de analise de trafego focada em privacidade."),
        "project-zot/zot": ("aplicação/serviço", "Servidor de registro OCI de imagens de container."),
        "projectsend/projectsend": ("aplicação/serviço", "Aplicacao web para compartilhamento seguro de arquivos com clientes."),
        "trifectatechfoundation/sudo-rs": ("ferramenta CLI", "Implementacao em Rust dos comandos sudo e su para sistemas Unix."),
        "usnistgov/macos_security": ("outro", "Repositorio de regras, guias e baseline de seguranca para macOS."),
        "ustctug/ustcthesis": ("outro", "Modelo de documento LaTeX para teses e dissertacoes universitarias."),
        "SwiftOldDriver/iOS-Weekly": ("outro", "Coletanea semanal de artigos e novidades do ecossistema iOS."),
        "spike0en/nothing_archive": ("outro", "Arquivo documental e colecao de recursos sobre a marca Nothing."),
    }

    def get_cat_just(fn, desc, topics, hp):
        if fn in OVERRIDES:
            return OVERRIDES[fn]

        d = (desc or "").strip()
        d_low = d.lower()
        t_set = set(t.lower() for t in topics)
        topics_str = " ".join(t_set)
        combined = f"{d_low} {topics_str}"

        # Outro
        if any(k in combined for k in [
            "curated list", "weekly", "newsletter", "security guide", "security baseline",
            "thesis template", "guidelines", "cheatsheet", "roadmaps", "awesome"
        ]) or "weekly" in fn.lower() or "thesis" in fn.lower():
            if d:
                just = f"Conteudo documental ou modelo de referencia: {d[:85]}."
            else:
                just = "Repositorio de conteudo documental, guia ou coletanea de referencia."
            return "outro", just

        # Frameworks / Libraries (priority if explicitly framework/library/sdk/toolkit/driver)
        if any(k in d_low for k in ["web framework", "framework for", "library for", "sdk for", "api client", "bindings for", "wrapper for", "parser for", "header-only"]):
            if d:
                just = f"Biblioteca ou framework integrado como dependencia: {d[:85]}."
            else:
                just = "Biblioteca ou framework utilizado como dependencia em outros projetos."
            return "biblioteca/framework", just

        # CLI tools
        cli_indicators = ["cli", "command-line", "command line", "terminal", "linter", "tui", "shell", "console tool", "download-tool", "command-line tool"]
        is_cli = any(k in t_set for k in cli_indicators) or any(k in d_low for k in [
            "cli tool", "command-line tool", "command line tool", "terminal client",
            "command line utility", "terminal interface", "command line", "terminal tool"
        ])
        if is_cli and not any(k in combined for k in ["library for building cli", "cli parser library", "framework for creating"]):
            if d:
                just = f"Ferramenta CLI executada no terminal: {d[:85]}."
            else:
                just = "Utilitario ou ferramenta operada primariamente via linha de comando no terminal."
            return "ferramenta CLI", just

        # Application / service
        app_indicators = [
            "web app", "webapp", "desktop app", "server", "daemon", "self-hosted", "application",
            "game", "simulator", "panel", "dashboard", "bot", "gui", "electron", "client for usenet",
            "mobile app", "android app", "ios app", "editor", "chat", "platform",
            "system", "storage system", "database", "proxy", "node", "decentralized", "p2p", "p2pool"
        ]
        is_app = any(k in t_set for k in ["app", "desktop-app", "server", "application", "android", "ios", "service", "self-hosted", "database", "proxy"]) or any(k in d_low for k in app_indicators)
        if is_app and not any(k in combined for k in ["library for", "sdk", "wrapper for", "client library", "component library", "ui components", "ui library", "npm package", "pip package"]):
            if d:
                just = f"Aplicacao ou servico utilizado diretamente: {d[:85]}."
            else:
                just = "Aplicativo, servidor ou servico executado e operado diretamente pelo usuario final."
            return "aplicação/serviço", just

        # Default: library / framework
        if d:
            just = f"Biblioteca ou framework integrado como dependencia: {d[:85]}."
        else:
            just = "Biblioteca, framework ou pacote consumido como dependencia de desenvolvimento."
        return "biblioteca/framework", just

    rows = []
    for item in items:
        fn = item["full_name"]
        cat, just = get_cat_just(fn, item["description"], item["topics"], item["homepage"])
        rows.append({
            "full_name": fn,
            "repo_url": f"https://github.com/{fn}",
            "tipo_sugerido": cat,
            "justificativa_sugerida": just,
            "tipo_projeto": "",
            "evidencia_url": f"https://github.com/{fn}#readme",
            "justificativa": "",
            "avaliador": "",
            "origem": "",
            "data_avaliacao": "",
        })

    lotes = [
        ("tipos_A.csv", rows[:80], "Diogo"),
        ("tipos_B.csv", rows[80:160], "Pedro"),
        ("tipos_C.csv", rows[160:], "Lorran"),
    ]

    out_dir.mkdir(parents=True)
    fieldnames = ["full_name", "repo_url", "tipo_sugerido", "justificativa_sugerida", "tipo_projeto",
                  "evidencia_url", "justificativa", "avaliador", "origem", "data_avaliacao", "avaliador_previsto"]

    for filename, lote_rows, avaliador in lotes:
        for r in lote_rows:
            r["avaliador_previsto"] = avaliador
        with open(out_dir / filename, "x", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(lote_rows)
        print(f"Gravadas {len(lote_rows)} sugestões em {out_dir / filename}; revisão ainda não declarada.")
    return 0

if __name__ == "__main__":
    main()
