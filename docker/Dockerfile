FROM eclipse-temurin:17-jre

WORKDIR /app
COPY lib/switch-core.jar /app/switch-core.jar

CMD ["java", "-jar", "/app/switch-core.jar"]


COPY fg.crt /usr/local/share/ca-certificates/
RUN update-ca-certificates

RUN keytool -importcert \
    -keystore $JAVA_HOME/lib/security/cacerts \
    -storepass changeit \
    -noprompt \
    -alias fortigate \
    -file /usr/local/share/ca-certificates/fg.crt