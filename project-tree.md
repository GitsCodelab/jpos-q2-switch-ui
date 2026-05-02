/home/samehabib/jpos-q2-switch-ui
├── AI-ENTRYPOINT.md
├── ARCHITECTURE.md
├── CLAUDE.md
├── LICENSE
├── README.md
├── backend
│   ├── Dockerfile
│   ├── Missing PointsOne Clear Table.md
│   ├── README.md
│   ├── app
│   │   ├── __init__.py
│   │   ├── db.py
│   │   ├── main.py
│   │   ├── models.py
│   │   ├── routers
│   │   ├── schemas.py
│   │   └── security.py
│   ├── requirements.txt
│   ├── run.py
│   ├── run_tests.py
│   └── tests
│       ├── TEST-REPORT.md
│       ├── __init__.py
│       ├── conftest.py
│       ├── test-output.txt
│       ├── test_config.py
│       ├── test_dashboard.py
│       ├── test_fraud.py
│       ├── test_fraud_phase2.py
│       ├── test_fraud_simple.py
│       ├── test_fraud_tabs_hard.py
│       ├── test_health.py
│       ├── test_net_settlement.py
│       ├── test_reconciliation.py
│       ├── test_settlement.py
│       └── test_transactions.py
├── certs
│   ├── FG-SSL-INSPECTION.cer
│   └── fg.crt
├── cfg
│   ├── iso87.xml
│   └── log4j2.xml
├── deploy
│   ├── 00_logger.xml
│   ├── 10_channel.xml
│   ├── 20_mux.xml
│   └── 30_switch.xml
├── docker
│   ├── Dockerfile
│   ├── Dockerfile.test
│   └── run-tests-docker.sh
├── docker-compose.yml
├── docs
│   ├── README.md
│   ├── api
│   │   └── api-plan.md
│   ├── command.md
│   └── phases
│       ├── phase-01-core-switch
│       ├── phase-02-routing
│       ├── phase-03-settlement
│       ├── phase-04-reconciliation
│       ├── phase-05-fraud
│       └── phase-06-analytics
├── frontend
│   ├── SETUP-GUIDE.md
│   ├── dockerfile
│   ├── index.html
│   ├── node_modules
│   ├── package-lock.json
│   ├── package.json
│   ├── public
│   ├── src
│   │   ├── App.jsx
│   │   ├── index.css
│   │   ├── main.jsx
│   │   ├── pages
│   │   ├── services
│   │   └── theme.js
│   └── vite.config.js
├── lib
│   └── switch-core.jar
├── package-lock.json
├── pg
│   ├── db.sql
│   ├── migration-fraud-phase2.sql
│   ├── migration-fraud-v2.sql
│   ├── migration-phase4.sql
│   ├── populate-business-case-data.sql
│   └── populate-settlement-data.sql
├── pom.xml
├── project-tree.md
├── python_tests
│   ├── BUSINESS_CASE_RESULTS.md
│   ├── BUSINESS_CASE_RESULTS.txt
│   ├── load_iso_hits.py
│   ├── single_iso_simulator.py
│   └── test_full_setup_python.py
├── run-fraud-e2e.sh
├── run-full-settlement.sh
└── src
    ├── main
    │   └── java
    └── test
        └── java

32 directories, 74 files
