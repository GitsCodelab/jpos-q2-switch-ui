# jPOS-EE Q2 Switch

This setup is rebuilt on top of the jPOS-EE stack (`org.jpos.ee`) and keeps your requested switch structure.

## Structure

- `deploy/`: Q2 deployment descriptors
- `cfg/`: ISO8583 packager descriptor
- `lib/`: packaged JAR output (`switch-core.jar`)
- `src/main/java/com/switch`: listener, services, DAO, model, and crypto utils
- `src/test/java/com/switch`: unit tests
- `docker/`: runtime container image definition

## Prerequisites

- Java 17+
- Maven 3.9+

## Commands

```bash
mvn clean test
mvn clean package
```

The package phase writes `lib/switch-core.jar`.
