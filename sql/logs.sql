CREATE TABLE OPSINTEL.PIPELINE_LOGS (
    LOG_ID DECIMAL(18,0),
    RUN_ID DECIMAL(18,0),
    LOG_LEVEL VARCHAR(20),
    LOG_MESSAGE VARCHAR(500),
    LOG_TIME TIMESTAMP
);

INSERT INTO OPSINTEL.PIPELINE_LOGS
VALUES (
    1,
    1,
    'INFO',
    'Pipeline started; expected 100 source rows',
    CURRENT_TIMESTAMP
);

INSERT INTO OPSINTEL.PIPELINE_LOGS
VALUES (
    2,
    1,
    'WARN',
    'Source returned only 80 rows',
    CURRENT_TIMESTAMP
);

INSERT INTO OPSINTEL.PIPELINE_LOGS
VALUES (
    3,
    1,
    'ERROR',
    'Import ended before all expected rows were processed',
    CURRENT_TIMESTAMP
);
