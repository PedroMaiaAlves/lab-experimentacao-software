FROM maven:3.9.11-eclipse-temurin-17 AS builder

ARG OMB_REVISION=5b1fa70951a323da26bd587174b58bb2c65b0b5c
RUN git clone https://github.com/openmessaging/benchmark.git /src/omb \
    && cd /src/omb \
    && git checkout "${OMB_REVISION}"
COPY omb-seconds.patch /tmp/omb-seconds.patch
RUN cd /src/omb \
    && git apply /tmp/omb-seconds.patch \
    && mvn -DskipTests -Dcheckstyle.skip -Dspotless.check.skip -Dspotbugs.skip package

FROM eclipse-temurin:17-jre
COPY --from=builder /src/omb/package/target/openmessaging-benchmark-*-bin.tar.gz /tmp/omb.tar.gz
RUN mkdir /benchmark \
    && tar -xzf /tmp/omb.tar.gz --strip-components=1 -C /benchmark \
    && rm /tmp/omb.tar.gz
WORKDIR /benchmark
ENTRYPOINT ["/benchmark/bin/benchmark"]
