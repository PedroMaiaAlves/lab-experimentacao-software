FROM maven:3.9.11-eclipse-temurin-17 AS builder

ARG OMB_REVISION=5b1fa70951a323da26bd587174b58bb2c65b0b5c
RUN git clone https://github.com/openmessaging/benchmark.git /src/omb \
    && cd /src/omb \
    && git checkout "${OMB_REVISION}"
COPY omb-seconds.patch /tmp/omb-seconds.patch
COPY omb-rabbitmq-timestamp-ms.patch /tmp/omb-rabbitmq-timestamp-ms.patch
COPY prune-drivers.awk /tmp/prune-drivers.awk
RUN cd /src/omb \
    && git apply /tmp/omb-seconds.patch \
    && git apply /tmp/omb-rabbitmq-timestamp-ms.patch \
    && awk -f /tmp/prune-drivers.awk benchmark-framework/pom.xml > benchmark-framework/pom.xml.new \
    && mv benchmark-framework/pom.xml.new benchmark-framework/pom.xml \
    && mvn -pl benchmark-framework -am -DskipTests -Dcheckstyle.skip -Dspotless.check.skip -Dspotbugs.skip install \
    && mkdir -p /out/lib \
    && mvn -pl benchmark-framework -DincludeScope=runtime -DoutputDirectory=/out/lib dependency:copy-dependencies \
    && cp benchmark-framework/target/benchmark-framework-*.jar /out/lib/

FROM eclipse-temurin:17-jre
COPY --from=builder /out/lib /benchmark/lib
WORKDIR /benchmark
ENTRYPOINT ["java", "-server", "-Xms512m", "-Xmx1536m", "-XX:+UseG1GC", "-cp", "/benchmark/lib/*", "io.openmessaging.benchmark.Benchmark"]
