# Command Reference - jpos-q2-switch

## 1) Build

```bash
cd /home/samehabib/jpos-q2-switch
mvn clean test
mvn clean package
```

Quick package without tests:

```bash
cd /home/samehabib/jpos-q2-switch
mvn clean package -DskipTests
```

## 2) Docker Runtime

Start/refresh stack:

```bash
cd /home/samehabib/jpos-q2-switch
docker compose up --build -d
```

Stop stack:

```bash
cd /home/samehabib/jpos-q2-switch
docker compose down
```

Logs:

```bash
cd /home/samehabib/jpos-q2-switch
docker compose logs -f switch
```

Port reset (if 9000 busy):

```bash
cd /home/samehabib/jpos-q2-switch
pkill -f 'org.jpos.q2.Q2' || true
fuser -k 9000/tcp || true
docker compose down --remove-orphans
docker compose up --build -d
```

## 3) Schema / DB

Initialize schema:

```bash
cd /home/samehabib/jpos-q2-switch
docker compose exec -T jpos-postgresql psql -U postgres -f /docker-entrypoint-initdb.d/db.sql
```

Latest transactions/events snapshot:

```bash
cd /home/samehabib/jpos-q2-switch
docker compose exec -T jpos-postgresql psql -U postgres -d jpos -c "SELECT id,stan,rrn,mti,rc,status,final_status,created_at FROM transactions ORDER BY id DESC LIMIT 10;"
docker compose exec -T jpos-postgresql psql -U postgres -d jpos -c "SELECT id,stan,event_type,left(request_iso,120) AS request_head,left(response_iso,120) AS response_head,created_at FROM transaction_events ORDER BY id DESC LIMIT 10;"
```

## 4) Java + Python Validation

All Java tests:

```bash
cd /home/samehabib/jpos-q2-switch
mvn -q test
```

All Python tests:

```bash
cd /home/samehabib/jpos-q2-switch
source .venv/bin/activate
python -m pytest -s python_tests/ -q
```

Run validation in Docker (host UID/GID):

```bash
cd /home/samehabib/jpos-q2-switch
bash docker/run-tests-docker.sh
```

## 5) Reconciliation

Run reconciliation runner:

```bash
cd /home/samehabib/jpos-q2-switch
docker compose up -d
mvn -q -DskipTests org.codehaus.mojo:exec-maven-plugin:3.5.0:java \
  -Dexec.mainClass=com.qswitch.recon.ReconciliationRunner
```

Run reconciliation unit tests only:

```bash
cd /home/samehabib/jpos-q2-switch
mvn -q -Dtest=ReconciliationServiceTest test
```

## 6) Auto-Reversal & Recovery

Run auto-reversal runner:

```bash
cd /home/samehabib/jpos-q2-switch
docker compose up -d
mvn -q -DskipTests org.codehaus.mojo:exec-maven-plugin:3.5.0:java \
  -Dexec.mainClass=com.qswitch.recon.AutoReversalRunner \
  -Drecon.mux.name=mux.acquirer-mux \
  -Drecon.reversal.threshold.seconds=60
```

Run auto-reversal + reconciliation tests:

```bash
cd /home/samehabib/jpos-q2-switch
mvn -q -Dtest=ReconciliationServiceTest,AutoReversalServiceTest test
```

## 7) Optional Local Q2 Debug (non-docker)

```bash
cd /home/samehabib/jpos-q2-switch
pkill -f 'org.jpos.q2.Q2' || true
: > logs/q2.log
nohup java -Dswitch.listener.debug=true -cp "$(cat .cp.txt):target/classes" org.jpos.q2.Q2 > q2.log 2>&1 &
```
