FROM eclipse-temurin:25-jdk

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends maven ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Trust corporate SSL inspection certificate for Maven/JDK HTTPS downloads.
COPY certs/FG-SSL-INSPECTION.cer /usr/local/share/ca-certificates/FG-SSL-INSPECTION.crt
RUN update-ca-certificates \
    && keytool -importcert -noprompt \
        -alias fg-ssl-inspection \
        -file /usr/local/share/ca-certificates/FG-SSL-INSPECTION.crt \
        -cacerts -storepass changeit

COPY pom.xml /app/pom.xml
COPY src /app/src
# COPY cfg /app/cfg
COPY deploy /app/deploy

RUN mkdir -p /app/logs

RUN mvn -q -DskipTests package dependency:build-classpath -Dmdep.outputFile=.cp.txt

CMD ["sh", "-lc", "java $JAVA_OPTS -Dlog4j2.configurationFile=cfg/log4j2.xml -cp \"target/classes:$(cat .cp.txt)\" org.jpos.q2.Q2 -d deploy -n Q2-DOCKER"]