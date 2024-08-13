CREATE SCHEMA mimiciii;
SET search_path TO mimiciii;

CREATE TABLE admissions (
    row_id INT NOT NULL,
    subject_id INT NOT NULL,
    hadm_id INT NOT NULL,
    admittime TIMESTAMP NOT NULL,
    dischtime TIMESTAMP,
    deathtime TIMESTAMP,
    admission_type VARCHAR(50) NOT NULL,
    admission_location VARCHAR(50),
    discharge_location VARCHAR(50),
    insurance VARCHAR(255),
    language VARCHAR(10),
    religion VARCHAR(50),
    marital_status VARCHAR(50),
    ethnicity VARCHAR(200),
    edregtime TIMESTAMP,
    edouttime TIMESTAMP,
    diagnosis VARCHAR(255),
    hospital_expire_flag SMALLINT,
    has_chartevents_data SMALLINT,
    CONSTRAINT admissions_rowid_pk PRIMARY KEY (row_id),
    CONSTRAINT admissions_hadm_id_unique UNIQUE (hadm_id)
);

COPY admissions FROM 'F:\C\Data\mimic-iii\csv\ADMISSIONS.csv' DELIMITER ',' CSV HEADER;

select  subject_id, count (hadm_id) from admissions
group by subject_id
order by count(hadm_id) desc

CREATE TABLE labevents (
    row_id INT NOT NULL,
    subject_id INT NOT NULL,
    hadm_id INT,
    itemid INT NOT NULL,
    charttime TIMESTAMP,
    value VARCHAR(200),
    valuenum DOUBLE PRECISION,
    valueuom VARCHAR(20),
    flag VARCHAR(20),
    CONSTRAINT labevents_rowid_pk PRIMARY KEY (row_id)
);

COPY labevents FROM 'F:\C\Data\mimic-iii\csv\LABEVENTS.csv' DELIMITER ',' CSV HEADER;

select count(*) from labevents

CREATE TABLE noteevents (
    row_id INT NOT NULL,
    subject_id INT NOT NULL,
    hadm_id INT,
    chartdate TIMESTAMP,
    charttime TIMESTAMP,
    storetime TIMESTAMP,
    category VARCHAR(50),
    description VARCHAR(255),
    cgid INT,
    iserror CHAR(1),
    text TEXT,
    CONSTRAINT noteevents_rowid_pk PRIMARY KEY (row_id)
);

COPY noteevents FROM 'F:\C\Data\mimic-iii\csv\NOTEEVENTS.csv' DELIMITER ',' CSV HEADER;

select count(*) from noteevents

CREATE TABLE patients (
    row_id INT NOT NULL,
    subject_id INT NOT NULL,
    gender VARCHAR(5) NOT NULL,
    dob TIMESTAMP NOT NULL,
    dod TIMESTAMP,
    dod_hosp TIMESTAMP,
    dod_ssn TIMESTAMP,
    expire_flag INT NOT NULL,
    CONSTRAINT patients_rowid_pk PRIMARY KEY (row_id),
    CONSTRAINT patients_subject_id_unique UNIQUE (subject_id)
);

COPY patients FROM 'f:\C\Data\mimic-iii\csv\PATIENTS.csv' DELIMITER ',' CSV HEADER;


CREATE TABLE prescriptions (
    row_id INT NOT NULL,
    subject_id INT NOT NULL,
    hadm_id INT NOT NULL,
    icustay_id INT,
    startdate TIMESTAMP,
    enddate TIMESTAMP,
    drug_type VARCHAR(100),
    drug VARCHAR(100),
    drug_name_poe VARCHAR(100),
    drug_name_generic VARCHAR(100),
    formulary_drug_cd VARCHAR(120),
    gsn VARCHAR(200),
    ndc VARCHAR(120),
    prod_strength VARCHAR(120),
    dose_val_rx VARCHAR(120),
    dose_unit_rx VARCHAR(120),
    form_val_disp VARCHAR(120),
    form_unit_disp VARCHAR(120),
    route VARCHAR(120),
    CONSTRAINT prescriptions_rowid_pk PRIMARY KEY (row_id)
);

COPY prescriptions FROM 'f:\C\Data\mimic-iii\csv\PRESCRIPTIONS.csv' DELIMITER ',' CSV HEADER;


CREATE TABLE procedures_icd (
    row_id INT NOT NULL,
    subject_id INT NOT NULL,
    hadm_id INT NOT NULL,
    seq_num INT NOT NULL,
    icd9_code VARCHAR(10),
    CONSTRAINT procedures_icd_rowid_pk PRIMARY KEY (row_id)
);

COPY PROCEDURES_ICD FROM 'f:\C\Data\mimic-iii\csv\PROCEDURES_ICD.csv' DELIMITER ',' CSV HEADER;


CREATE TABLE diagnoses_icd (
    row_id INT NOT NULL,
    subject_id INT NOT NULL,
    hadm_id INT NOT NULL,
    seq_num INT,
    icd9_code VARCHAR(10),
    CONSTRAINT diagnoses_icd_rowid_pk PRIMARY KEY (row_id)
);

COPY DIAGNOSES_ICD FROM 'f:\C\Data\mimic-iii\csv\DIAGNOSES_ICD.csv' DELIMITER ',' CSV HEADER;
