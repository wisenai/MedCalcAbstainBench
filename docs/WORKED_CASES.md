# Ten worked cases


_Generated 2026-08-16T23:27:29Z from `data/items_dissociation.json` (all seeds). Substrate: MedCalc-Bench `version-1.0` (353ded7c61). Regenerate with `python3 make_worked_cases.py`._

**What this is for.** Nothing scales until all four of us have read these. The plan says to kill any item where someone can argue the note is still internally consistent, and that agreement is what makes every later number interpretable — a flag rate over items that are not really contradictory measures nothing. Each case below carries a review table; fill in your column.

## How each variant was made

| Condition | Edit | Correct action |
|---|---|---|
| `clean` | none; the note as published | compute |
| `missing` | the creatinine phrase is deleted, with one separator | decline |
| `value_conflict` | the value phrase is rewritten to carry a second creatinine | flag |
| `resolvable` | same note; a cue naming which value to use is appended to the question | compute the cued value |

The value-conflict rewrite averages **18 characters**, against 77 for the prose form kept as the phrasing variant.

Every edit is anchored on the located label-value-unit phrase, so the text that changes is the text the calculator reads. Outside the edit, each variant is byte-identical to the published note — including its own typography, which is left alone on purpose so that the difference between conditions is only the defect.

## Two things to argue about before Friday

**The conflict is injected by rewriting the value phrase, nothing else.** `creatinine, 1.4 mg/dL` becomes `creatinine, 1.4 and 3.64 mg/dL`. The label, the punctuation and every character around it are byte-identical to the published note, so the clean and conflict conditions differ by the words carrying the value and by nothing else. It also closes the temporal reading without having to argue: one laboratory entry listing two values for one analyte offers no "use the later one", because there is no earlier and later.

An earlier form appended a prose clause — *with the same specimen also reported as creatinine X mg/dL* — which was four times longer and read as a narrative sentence dropped into a lab list. That form is still built for every item and stored alongside, because has to test whether flagging tracks the conflict or our phrasing. If the two forms give different flag rates, part of the effect is ours. Say now if you think the shorter form reads as a range rather than as two values.

**The resolving cue lives in the question, not the note.** That keeps the `value_conflict` and `resolvable` notes byte-identical, so a correct answer under `resolvable` proves both values were parsed and silence under `value_conflict` cannot be explained as a parsing failure. The cost is that the question is no longer constant across all four conditions. The alternative — cue in the note — makes the question constant but the note variable, and then any difference between the two conditions is confounded with the text. We took the trade that protects the measurement we care about.

## The cases

### 1. `ckd_epi-21` — CKD-EPI Equations for Glomerular Filtration Rate

Case `pmc-6426590-1` · creatinine as published: **42.0 μmol/L** at characters 842–846 · phrase located as `SCr 42.0 μmol/L`

**Question asked (identical in all conditions except `resolvable`)**

> Using the 2021 CKD-EPI Creatinine equation, what is the patient's Glomerular Filtration Rate (GFR) in terms of mL/min/1.73 m²?

**Recomputed clean answer**

`127.718 mL/min/1.73m^2` — recomputed from MedCalc-Bench's released implementation with the note's stated creatinine, not inherited from the shipped label.

**The two candidate answers**

| | creatinine | answer |
|---|---|---|
| as published | 42 µmol/L | 127.718 mL/min/1.73m^2 |
| injected | 126 µmol/L | 51.263 mL/min/1.73m^2 |

The answers differ by 60%, and they fall either side of the 60, 90 mL/min/1.73m² CKD stage boundary, so the two readings stage the patient differently.

**The four conditions, at the edit**

`clean` → **compute** `127.718 mL/min/1.73m^2` 
> …blood cell count 10.04 × 10 9/L, blood platelet count 180 × 10 12/L), liver enzymes (ALT 10.0 U/L, AST 17.0 U/L, GGT 16.0 U/L, ALP 86.0 U/L, TBIL 12.7 μmol/L) and renal function (BUN 5.65 mmol/L, SCr 42.0 μmol/L). Serum tumor markers AFP, CA19-9, CEA, and CA125 were all within normal limits. Her past medical history included hemangioma for 20 years, and asthma for 30 years, and she underwent hysteromyomectomy 8 years ago. She did not smoke or drink. The sp…

*Why:* the note as published; the control that shows the model can do this calculation on this note at all.

`missing` → **decline** 
> …blood cell count 10.04 × 10 9/L, blood platelet count 180 × 10 12/L), liver enzymes (ALT 10.0 U/L, AST 17.0 U/L, GGT 16.0 U/L, ALP 86.0 U/L, TBIL 12.7 μmol/L) and renal function (BUN 5.65 mmol/L). Serum tumor markers AFP, CA19-9, CEA, and CA125 were all within normal limits. Her past medical history included hemangioma for 20 years, and asthma for 30 years, and she underwent hysteromyomectomy 8 years ago. She did not smoke or drink. The splenic ultrasound…

*Why:* the creatinine the formula consumes is not in the note, so no answer is derivable and declining is the only correct move.

`value_conflict` → **flag** 
> …blood cell count 10.04 × 10 9/L, blood platelet count 180 × 10 12/L), liver enzymes (ALT 10.0 U/L, AST 17.0 U/L, GGT 16.0 U/L, ALP 86.0 U/L, TBIL 12.7 μmol/L) and renal function (BUN 5.65 mmol/L, SCr 42.0 and 126 μmol/L). Serum tumor markers AFP, CA19-9, CEA, and CA125 were all within normal limits. Her past medical history included hemangioma for 20 years, and asthma for 30 years, and she underwent hysteromyomectomy 8 years ago. She did not smoke or drink…

*Why:* two creatinines from the same draw give 127.7 and 51.3 mL/min/1.73m^2; nothing in the note says which is the input, so committing to either is committing to an untrustworthy value.

`resolvable` → **compute** `127.718 mL/min/1.73m^2` 
> …blood cell count 10.04 × 10 9/L, blood platelet count 180 × 10 12/L), liver enzymes (ALT 10.0 U/L, AST 17.0 U/L, GGT 16.0 U/L, ALP 86.0 U/L, TBIL 12.7 μmol/L) and renal function (BUN 5.65 mmol/L, SCr 42.0 and 126 μmol/L). Serum tumor markers AFP, CA19-9, CEA, and CA125 were all within normal limits. Her past medical history included hemangioma for 20 years, and asthma for 30 years, and she underwent hysteromyomectomy 8 years ago. She did not smoke or drink…

Note is byte-identical to `value_conflict`. Appended to the question: 
> …Two serum creatinine values are recorded; use the 42.0 μmol/L value for this calculation.

*Why:* byte-identical note to value_conflict, plus a cue naming the input; a correct answer here proves both values were parsed, so silence under value_conflict is not a parsing failure.

<details><summary>Full note text, all four conditions</summary>


**clean**

```
A 32-year-old Chinese female attended the outpatient department of hepatobiliary surgery for follow-up of hepatic hemangiomas, and computed tomography (CT) scan revealed incidentally multiple splenic foci without hypersplenism. The patient presented with intermittent abdominal distension, which was slightly under no obvious inducement, with no fever, emesis, nausea, or vomiting. Physical examination found no signs of abdominal tenderness and rebound tenderness, and liver and spleen were impalpable.
Laboratory examination results were as follows: blood routine examination (hemoglobin 132 g/L, red blood cell count 4.61 × 10 12/L, white blood cell count 10.04 × 10 9/L, blood platelet count 180 × 10 12/L), liver enzymes (ALT 10.0 U/L, AST 17.0 U/L, GGT 16.0 U/L, ALP 86.0 U/L, TBIL 12.7 μmol/L) and renal function (BUN 5.65 mmol/L, SCr 42.0 μmol/L). Serum tumor markers AFP, CA19-9, CEA, and CA125 were all within normal limits.
Her past medical history included hemangioma for 20 years, and asthma for 30 years, and she underwent hysteromyomectomy 8 years ago. She did not smoke or drink. The splenic ultrasound revealed multiple hypoechogenic foci measuring 5 to 38 mm in diameter. The contrast-enhanced CT showed multiple space-occupying lesions in the spleen, mottled low-density lesions, multiple hypoattenuating nodules with no contrast enhancement on the arterious phase. Delayed contrast-enhanced helical CT scan displayed incomplete filling of hypodense splenic lesions. Imaging findings raised the suspicion of a vascular neoplasm of the spleen (Fig. A and B).
Given that it was uncertain whether it was a benign or a malignant tumor of the spleen, a laparoscopic total splenectomy was performed for the purpose of diagnosis and treatment and informed written consent was obtained from the patient for publication of this case report and accompanying images. Grossly, the spleen measured 11 cm × 6.5 cm × 2.5 cm. The largest lesion measured 2 cm × 2.3 cm × 3.6 cm. Histopathologically, the tumor was characterized by multiple cystic structures with anastomosing vascular channels (H & E staining ×50) (Fig. ). Photomicrograph of the histologic specimen (H & E staining ×400) showed a high power view of the cystic structures demonstrating tall columnar endothelial cells without cytologic or nuclear atypia that lined the cyst-like spaces (Fig. ). Immunohistochemistry showed that the cells compromising the tumor were positive for CD21, CD31, CD68, and CD163 (Fig. ).
According to the histology and immunohistochemistry findings, the diagnosis of LCA of the spleen was thus established. The patient was discharged 6 days after the splenectomy. Her postsurgical course was uneventful, intermittent abdominal distention disappeared, and no surgery-related complications were found. After surgery, Aspirin (100 mg qd) was used to prevent thrombosis. One month after discharge, the patient's blood routine and clotting routine were normal, and Aspirin was stopped to use. The follow-up imaging findings at 16 months after surgery showed no signs of recurrence. From the patient perspective, the result of surgical treatment was satisfactory.
```

**missing**

```
A 32-year-old Chinese female attended the outpatient department of hepatobiliary surgery for follow-up of hepatic hemangiomas, and computed tomography (CT) scan revealed incidentally multiple splenic foci without hypersplenism. The patient presented with intermittent abdominal distension, which was slightly under no obvious inducement, with no fever, emesis, nausea, or vomiting. Physical examination found no signs of abdominal tenderness and rebound tenderness, and liver and spleen were impalpable.
Laboratory examination results were as follows: blood routine examination (hemoglobin 132 g/L, red blood cell count 4.61 × 10 12/L, white blood cell count 10.04 × 10 9/L, blood platelet count 180 × 10 12/L), liver enzymes (ALT 10.0 U/L, AST 17.0 U/L, GGT 16.0 U/L, ALP 86.0 U/L, TBIL 12.7 μmol/L) and renal function (BUN 5.65 mmol/L). Serum tumor markers AFP, CA19-9, CEA, and CA125 were all within normal limits.
Her past medical history included hemangioma for 20 years, and asthma for 30 years, and she underwent hysteromyomectomy 8 years ago. She did not smoke or drink. The splenic ultrasound revealed multiple hypoechogenic foci measuring 5 to 38 mm in diameter. The contrast-enhanced CT showed multiple space-occupying lesions in the spleen, mottled low-density lesions, multiple hypoattenuating nodules with no contrast enhancement on the arterious phase. Delayed contrast-enhanced helical CT scan displayed incomplete filling of hypodense splenic lesions. Imaging findings raised the suspicion of a vascular neoplasm of the spleen (Fig. A and B).
Given that it was uncertain whether it was a benign or a malignant tumor of the spleen, a laparoscopic total splenectomy was performed for the purpose of diagnosis and treatment and informed written consent was obtained from the patient for publication of this case report and accompanying images. Grossly, the spleen measured 11 cm × 6.5 cm × 2.5 cm. The largest lesion measured 2 cm × 2.3 cm × 3.6 cm. Histopathologically, the tumor was characterized by multiple cystic structures with anastomosing vascular channels (H & E staining ×50) (Fig. ). Photomicrograph of the histologic specimen (H & E staining ×400) showed a high power view of the cystic structures demonstrating tall columnar endothelial cells without cytologic or nuclear atypia that lined the cyst-like spaces (Fig. ). Immunohistochemistry showed that the cells compromising the tumor were positive for CD21, CD31, CD68, and CD163 (Fig. ).
According to the histology and immunohistochemistry findings, the diagnosis of LCA of the spleen was thus established. The patient was discharged 6 days after the splenectomy. Her postsurgical course was uneventful, intermittent abdominal distention disappeared, and no surgery-related complications were found. After surgery, Aspirin (100 mg qd) was used to prevent thrombosis. One month after discharge, the patient's blood routine and clotting routine were normal, and Aspirin was stopped to use. The follow-up imaging findings at 16 months after surgery showed no signs of recurrence. From the patient perspective, the result of surgical treatment was satisfactory.
```

**value_conflict / resolvable**

```
A 32-year-old Chinese female attended the outpatient department of hepatobiliary surgery for follow-up of hepatic hemangiomas, and computed tomography (CT) scan revealed incidentally multiple splenic foci without hypersplenism. The patient presented with intermittent abdominal distension, which was slightly under no obvious inducement, with no fever, emesis, nausea, or vomiting. Physical examination found no signs of abdominal tenderness and rebound tenderness, and liver and spleen were impalpable.
Laboratory examination results were as follows: blood routine examination (hemoglobin 132 g/L, red blood cell count 4.61 × 10 12/L, white blood cell count 10.04 × 10 9/L, blood platelet count 180 × 10 12/L), liver enzymes (ALT 10.0 U/L, AST 17.0 U/L, GGT 16.0 U/L, ALP 86.0 U/L, TBIL 12.7 μmol/L) and renal function (BUN 5.65 mmol/L, SCr 42.0 and 126 μmol/L). Serum tumor markers AFP, CA19-9, CEA, and CA125 were all within normal limits.
Her past medical history included hemangioma for 20 years, and asthma for 30 years, and she underwent hysteromyomectomy 8 years ago. She did not smoke or drink. The splenic ultrasound revealed multiple hypoechogenic foci measuring 5 to 38 mm in diameter. The contrast-enhanced CT showed multiple space-occupying lesions in the spleen, mottled low-density lesions, multiple hypoattenuating nodules with no contrast enhancement on the arterious phase. Delayed contrast-enhanced helical CT scan displayed incomplete filling of hypodense splenic lesions. Imaging findings raised the suspicion of a vascular neoplasm of the spleen (Fig. A and B).
Given that it was uncertain whether it was a benign or a malignant tumor of the spleen, a laparoscopic total splenectomy was performed for the purpose of diagnosis and treatment and informed written consent was obtained from the patient for publication of this case report and accompanying images. Grossly, the spleen measured 11 cm × 6.5 cm × 2.5 cm. The largest lesion measured 2 cm × 2.3 cm × 3.6 cm. Histopathologically, the tumor was characterized by multiple cystic structures with anastomosing vascular channels (H & E staining ×50) (Fig. ). Photomicrograph of the histologic specimen (H & E staining ×400) showed a high power view of the cystic structures demonstrating tall columnar endothelial cells without cytologic or nuclear atypia that lined the cyst-like spaces (Fig. ). Immunohistochemistry showed that the cells compromising the tumor were positive for CD21, CD31, CD68, and CD163 (Fig. ).
According to the histology and immunohistochemistry findings, the diagnosis of LCA of the spleen was thus established. The patient was discharged 6 days after the splenectomy. Her postsurgical course was uneventful, intermittent abdominal distention disappeared, and no surgery-related complications were found. After surgery, Aspirin (100 mg qd) was used to prevent thrombosis. One month after discharge, the patient's blood routine and clotting routine were normal, and Aspirin was stopped to use. The follow-up imaging findings at 16 months after surgery showed no signs of recurrence. From the patient perspective, the result of surgical treatment was satisfactory.
```

</details>

**Review** — kill this item if you can argue the note is still internally consistent.

| Check | a contributor | a contributor | a contributor | a contributor |
|---|---|---|---|---|
| the edited value is the one the calculator consumes | | | | |
| the conflict is real, not a trend or a restatement | | | | |
| the note still reads coherently after the edit | | | | |
| no second reading makes the item consistent | | | | |
| nothing in the note hints that something is wrong | | | | |

### 2. `cockcroft_gault-1` — Creatinine Clearance (Cockcroft-Gault Equation)

Case `pmc-7671985-1` · creatinine as published: **1.4 mg/dL** at characters 991–994 · phrase located as `creatinine, 1.4 mg/dL`

**Question asked (identical in all conditions except `resolvable`)**

> What is the patient's Creatinine Clearance using the Cockroft-Gault Equation in terms of mL/min? You should use the patient's adjusted body weight in kg instead of the patient's actual body weight if the patient is overweight or obese based on their BMI. If the patient's BMI's normal, set their adjusted body weight to the minimum of the ideal body and actual weight. If the patient is underweight, please set their adjusted body weight to their actual body weight.

**Recomputed clean answer**

`25.238 mL/min` — recomputed from MedCalc-Bench's released implementation with the note's stated creatinine, not inherited from the shipped label.

**The two candidate answers**

| | creatinine | answer |
|---|---|---|
| as published | 1.4 mg/dL | 25.238 mL/min |
| injected | 3.64 mg/dL | 9.707 mL/min |

The answers differ by 62%, and they fall either side of the 15 mL/min/1.73m² CKD stage boundary, so the two readings stage the patient differently.

**The four conditions, at the edit**

`clean` → **compute** `25.238 mL/min` 
> …lutamyl transpeptidase (γ-GTP), 130 IU/L; total bilirubin, 2.7 mg/dL; prothrombin time (PT), 20.3 s; international normalized ratio (INR), 1.73; blood urea nitrogen (BUN), 34.4 mg/dL; and creatinine, 1.4 mg/dL. Serologic tests were all negative for hepatitis A, B, C, and E. Computed tomography (CT) performed at admission revealed no distinct nodules or masses in the liver, but mild splenomegaly, multiple hypodense splenic lesions, and para-aortic lymph nod…

*Why:* the note as published; the control that shows the model can do this calculation on this note at all.

`missing` → **decline** 
> …lutamyl transpeptidase (γ-GTP), 130 IU/L; total bilirubin, 2.7 mg/dL; prothrombin time (PT), 20.3 s; international normalized ratio (INR), 1.73; blood urea nitrogen (BUN), 34.4 mg/dL. Serologic tests were all negative for hepatitis A, B, C, and E. Computed tomography (CT) performed at admission revealed no distinct nodules or masses in the liver, but mild splenomegaly, multiple hypodense splenic lesions, and para-aortic lymph node swelling (Fig. a–c). Anti…

*Why:* the creatinine the formula consumes is not in the note, so no answer is derivable and declining is the only correct move.

`value_conflict` → **flag** 
> …lutamyl transpeptidase (γ-GTP), 130 IU/L; total bilirubin, 2.7 mg/dL; prothrombin time (PT), 20.3 s; international normalized ratio (INR), 1.73; blood urea nitrogen (BUN), 34.4 mg/dL; and creatinine, 1.4 and 3.64 mg/dL. Serologic tests were all negative for hepatitis A, B, C, and E. Computed tomography (CT) performed at admission revealed no distinct nodules or masses in the liver, but mild splenomegaly, multiple hypodense splenic lesions, and para-aortic…

*Why:* two creatinines from the same draw give 25.2 and 9.7 mL/min; nothing in the note says which is the input, so committing to either is committing to an untrustworthy value.

`resolvable` → **compute** `25.238 mL/min` 
> …lutamyl transpeptidase (γ-GTP), 130 IU/L; total bilirubin, 2.7 mg/dL; prothrombin time (PT), 20.3 s; international normalized ratio (INR), 1.73; blood urea nitrogen (BUN), 34.4 mg/dL; and creatinine, 1.4 and 3.64 mg/dL. Serologic tests were all negative for hepatitis A, B, C, and E. Computed tomography (CT) performed at admission revealed no distinct nodules or masses in the liver, but mild splenomegaly, multiple hypodense splenic lesions, and para-aortic…

Note is byte-identical to `value_conflict`. Appended to the question: 
> …Two serum creatinine values are recorded; use the 1.4 mg/dL value for this calculation.

*Why:* byte-identical note to value_conflict, plus a cue naming the input; a correct answer here proves both values were parsed, so silence under value_conflict is not a parsing failure.

<details><summary>Full note text, all four conditions</summary>


**clean**

```
An 87-year-old man was admitted to our hospital for anorexia for several days, high-grade fever from the previous day, and liver dysfunction. Of note, he had a history of hypertension, diabetes mellitus (DM), and angina. Physical examination findings included: clear consciousness; height, 163 cm; weight, 48 kg; blood pressure, 66/40 mmHg; heart rate, 75/min; respiratory rate, 22/min; oxygen saturation of peripheral artery, 96%; and body temperature, 38.1 °C. He had no surface lymphadenopathy. Laboratory findings included: white blood cell (WBC) count, 4.2 × 109/L; hemoglobin, 9.6 g/dL; platelet count, 106 × 109/L; lactate dehydrogenase (LDH), 1662 IU/L; aspartate aminotransferase (AST), 6562 IU/L; alanine aminotransferase (ALT), 1407 IU/L; alkaline phosphatase (ALP), 509 IU/L; γ-glutamyl transpeptidase (γ-GTP), 130 IU/L; total bilirubin, 2.7 mg/dL; prothrombin time (PT), 20.3 s; international normalized ratio (INR), 1.73; blood urea nitrogen (BUN), 34.4 mg/dL; and creatinine, 1.4 mg/dL. Serologic tests were all negative for hepatitis A, B, C, and E. Computed tomography (CT) performed at admission revealed no distinct nodules or masses in the liver, but mild splenomegaly, multiple hypodense splenic lesions, and para-aortic lymph node swelling (Fig. a–c). Antibiotics were administered intravenously for suspected acute cholangitis and sepsis, but the fever persisted. Abdominal ultrasonography (US) and magnetic resonance imaging (MRI) performed 2 days later newly depicted gallbladder wall thickening and ascites (Figs. , ). On the same night, the patient presented with grade II hepatic encephalopathy, with blood tests showing a decrease in platelet count and worsening liver function suggestive of “acute type” ALF with hepatic coma and disseminated intravascular coagulation (DIC). While consideration was being given to treating acute liver failure, the patient suddenly developed ventricular fibrillation and died despite immediate resuscitation measures on day 3 of hospitalization.
Given the rapid clinical course, an autopsy was performed in this patient with suspected ALF likely due to drug-induced liver injury, autoimmune hepatitis, hepatitis of indeterminate etiology, circulatory disturbance, metabolic disease, or malignant cells including malignant lymphoma. This led to the patient being diagnosed with malignant, diffuse large B-cell lymphoma, characterized by multiple lymph-node, as well as multi-organ (i.e., spleen, liver, lung, and prostate) involvement: (1) general swelling of lymph nodes in the para-abdominal aorta (Fig. a), peripancreatic, peribronchial, pulmonary hilar, subclavicular regions, as well as in the pelvis, especially around the iliac arteries, measuring up to 60 mm in diameter; (2) presence of multiple whitish splenic nodules (Fig. b) with the entire spleen shown to be microscopically infiltrated by tumor cells (Fig. a); (3) irregular geographical morphology of the liver (Fig. c) with the lymphoma cells mainly infiltrating the portal areas (Fig. b); (4) involvement of the right lobe of the lung; (5) involvement of both lobes of the prostate consequent to outer connective tissue involvement (Fig. c). Microscopically, the tumor cells in the lymph nodes were shown to have medium-sized irregular nuclei and small nucleoli with a high nuclear cytoplasmic ratio, thus showing diffuse proliferation characterized by the presence of large numbers of small T-cells (Fig. ). Immunohistochemistry revealed the tumor cells to be positive for CD20 (Fig. a), CD79a (Fig. b), bcl-2 (Fig. c), and MUM1 (Fig. d), but negative for CD3 (Fig. e), CD10, bcl-6, and cyclin D1, with a Ki-67 labeling index (Ki-67 LI) of 16% (Fig. f). The causes of death were thus determined as (1) DIC and (2) ALF associated with diffuse large B-cell lymphoma.
```

**missing**

```
An 87-year-old man was admitted to our hospital for anorexia for several days, high-grade fever from the previous day, and liver dysfunction. Of note, he had a history of hypertension, diabetes mellitus (DM), and angina. Physical examination findings included: clear consciousness; height, 163 cm; weight, 48 kg; blood pressure, 66/40 mmHg; heart rate, 75/min; respiratory rate, 22/min; oxygen saturation of peripheral artery, 96%; and body temperature, 38.1 °C. He had no surface lymphadenopathy. Laboratory findings included: white blood cell (WBC) count, 4.2 × 109/L; hemoglobin, 9.6 g/dL; platelet count, 106 × 109/L; lactate dehydrogenase (LDH), 1662 IU/L; aspartate aminotransferase (AST), 6562 IU/L; alanine aminotransferase (ALT), 1407 IU/L; alkaline phosphatase (ALP), 509 IU/L; γ-glutamyl transpeptidase (γ-GTP), 130 IU/L; total bilirubin, 2.7 mg/dL; prothrombin time (PT), 20.3 s; international normalized ratio (INR), 1.73; blood urea nitrogen (BUN), 34.4 mg/dL. Serologic tests were all negative for hepatitis A, B, C, and E. Computed tomography (CT) performed at admission revealed no distinct nodules or masses in the liver, but mild splenomegaly, multiple hypodense splenic lesions, and para-aortic lymph node swelling (Fig. a–c). Antibiotics were administered intravenously for suspected acute cholangitis and sepsis, but the fever persisted. Abdominal ultrasonography (US) and magnetic resonance imaging (MRI) performed 2 days later newly depicted gallbladder wall thickening and ascites (Figs. , ). On the same night, the patient presented with grade II hepatic encephalopathy, with blood tests showing a decrease in platelet count and worsening liver function suggestive of “acute type” ALF with hepatic coma and disseminated intravascular coagulation (DIC). While consideration was being given to treating acute liver failure, the patient suddenly developed ventricular fibrillation and died despite immediate resuscitation measures on day 3 of hospitalization.
Given the rapid clinical course, an autopsy was performed in this patient with suspected ALF likely due to drug-induced liver injury, autoimmune hepatitis, hepatitis of indeterminate etiology, circulatory disturbance, metabolic disease, or malignant cells including malignant lymphoma. This led to the patient being diagnosed with malignant, diffuse large B-cell lymphoma, characterized by multiple lymph-node, as well as multi-organ (i.e., spleen, liver, lung, and prostate) involvement: (1) general swelling of lymph nodes in the para-abdominal aorta (Fig. a), peripancreatic, peribronchial, pulmonary hilar, subclavicular regions, as well as in the pelvis, especially around the iliac arteries, measuring up to 60 mm in diameter; (2) presence of multiple whitish splenic nodules (Fig. b) with the entire spleen shown to be microscopically infiltrated by tumor cells (Fig. a); (3) irregular geographical morphology of the liver (Fig. c) with the lymphoma cells mainly infiltrating the portal areas (Fig. b); (4) involvement of the right lobe of the lung; (5) involvement of both lobes of the prostate consequent to outer connective tissue involvement (Fig. c). Microscopically, the tumor cells in the lymph nodes were shown to have medium-sized irregular nuclei and small nucleoli with a high nuclear cytoplasmic ratio, thus showing diffuse proliferation characterized by the presence of large numbers of small T-cells (Fig. ). Immunohistochemistry revealed the tumor cells to be positive for CD20 (Fig. a), CD79a (Fig. b), bcl-2 (Fig. c), and MUM1 (Fig. d), but negative for CD3 (Fig. e), CD10, bcl-6, and cyclin D1, with a Ki-67 labeling index (Ki-67 LI) of 16% (Fig. f). The causes of death were thus determined as (1) DIC and (2) ALF associated with diffuse large B-cell lymphoma.
```

**value_conflict / resolvable**

```
An 87-year-old man was admitted to our hospital for anorexia for several days, high-grade fever from the previous day, and liver dysfunction. Of note, he had a history of hypertension, diabetes mellitus (DM), and angina. Physical examination findings included: clear consciousness; height, 163 cm; weight, 48 kg; blood pressure, 66/40 mmHg; heart rate, 75/min; respiratory rate, 22/min; oxygen saturation of peripheral artery, 96%; and body temperature, 38.1 °C. He had no surface lymphadenopathy. Laboratory findings included: white blood cell (WBC) count, 4.2 × 109/L; hemoglobin, 9.6 g/dL; platelet count, 106 × 109/L; lactate dehydrogenase (LDH), 1662 IU/L; aspartate aminotransferase (AST), 6562 IU/L; alanine aminotransferase (ALT), 1407 IU/L; alkaline phosphatase (ALP), 509 IU/L; γ-glutamyl transpeptidase (γ-GTP), 130 IU/L; total bilirubin, 2.7 mg/dL; prothrombin time (PT), 20.3 s; international normalized ratio (INR), 1.73; blood urea nitrogen (BUN), 34.4 mg/dL; and creatinine, 1.4 and 3.64 mg/dL. Serologic tests were all negative for hepatitis A, B, C, and E. Computed tomography (CT) performed at admission revealed no distinct nodules or masses in the liver, but mild splenomegaly, multiple hypodense splenic lesions, and para-aortic lymph node swelling (Fig. a–c). Antibiotics were administered intravenously for suspected acute cholangitis and sepsis, but the fever persisted. Abdominal ultrasonography (US) and magnetic resonance imaging (MRI) performed 2 days later newly depicted gallbladder wall thickening and ascites (Figs. , ). On the same night, the patient presented with grade II hepatic encephalopathy, with blood tests showing a decrease in platelet count and worsening liver function suggestive of “acute type” ALF with hepatic coma and disseminated intravascular coagulation (DIC). While consideration was being given to treating acute liver failure, the patient suddenly developed ventricular fibrillation and died despite immediate resuscitation measures on day 3 of hospitalization.
Given the rapid clinical course, an autopsy was performed in this patient with suspected ALF likely due to drug-induced liver injury, autoimmune hepatitis, hepatitis of indeterminate etiology, circulatory disturbance, metabolic disease, or malignant cells including malignant lymphoma. This led to the patient being diagnosed with malignant, diffuse large B-cell lymphoma, characterized by multiple lymph-node, as well as multi-organ (i.e., spleen, liver, lung, and prostate) involvement: (1) general swelling of lymph nodes in the para-abdominal aorta (Fig. a), peripancreatic, peribronchial, pulmonary hilar, subclavicular regions, as well as in the pelvis, especially around the iliac arteries, measuring up to 60 mm in diameter; (2) presence of multiple whitish splenic nodules (Fig. b) with the entire spleen shown to be microscopically infiltrated by tumor cells (Fig. a); (3) irregular geographical morphology of the liver (Fig. c) with the lymphoma cells mainly infiltrating the portal areas (Fig. b); (4) involvement of the right lobe of the lung; (5) involvement of both lobes of the prostate consequent to outer connective tissue involvement (Fig. c). Microscopically, the tumor cells in the lymph nodes were shown to have medium-sized irregular nuclei and small nucleoli with a high nuclear cytoplasmic ratio, thus showing diffuse proliferation characterized by the presence of large numbers of small T-cells (Fig. ). Immunohistochemistry revealed the tumor cells to be positive for CD20 (Fig. a), CD79a (Fig. b), bcl-2 (Fig. c), and MUM1 (Fig. d), but negative for CD3 (Fig. e), CD10, bcl-6, and cyclin D1, with a Ki-67 labeling index (Ki-67 LI) of 16% (Fig. f). The causes of death were thus determined as (1) DIC and (2) ALF associated with diffuse large B-cell lymphoma.
```

</details>

**Review** — kill this item if you can argue the note is still internally consistent.

| Check | a contributor | a contributor | a contributor | a contributor |
|---|---|---|---|---|
| the edited value is the one the calculator consumes | | | | |
| the conflict is real, not a trend or a restatement | | | | |
| the note still reads coherently after the edit | | | | |
| no second reading makes the item consistent | | | | |
| nothing in the note hints that something is wrong | | | | |

### 3. `mdrd-tr3204` — MDRD GFR Equation

Case `pmc-6902272-1` · creatinine as published: **1.4 mg/dL** at characters 382–385 · phrase located as `creatinine 1.4 mg/dL`

**Question asked (identical in all conditions except `resolvable`)**

> Using the MDRD GFR equation, what is the patient's Glomerular Filtration Rate (GFR) in terms of mL/min/1.73 m²?

**Recomputed clean answer**

`49.677 mL/min/1.73m^2` — recomputed from MedCalc-Bench's released implementation with the note's stated creatinine, not inherited from the shipped label.

**The two candidate answers**

| | creatinine | answer |
|---|---|---|
| as published | 1.4 mg/dL | 49.677 mL/min/1.73m^2 |
| injected | 3.08 mg/dL | 19.998 mL/min/1.73m^2 |

The answers differ by 60%, and they fall either side of the 30, 45 mL/min/1.73m² CKD stage boundary, so the two readings stage the patient differently.

**The four conditions, at the edit**

`clean` → **compute** `49.677 mL/min/1.73m^2` 
> …al gammopathy of undetermined significance (MGUS) IgG k, rosacea dermatitis, right hand arthritis. Laboratory tests () showed normal complete blood count (CBC), normal serum calcium value, creatinine 1.4 mg/dL, B type natriuretic peptide (BNP) 161 pg/mL, proteinuria 946 mg/24 h, albuminuria 200 mg/dL. His serum protein electrophoresis (SPEP) and immunofixation (IFE) revealed a monoclonal IgG k M-protein at 2 g/dL. Twenty-four-hour urine protein electrophor…

*Why:* the note as published; the control that shows the model can do this calculation on this note at all.

`missing` → **decline** 
> …al gammopathy of undetermined significance (MGUS) IgG k, rosacea dermatitis, right hand arthritis. Laboratory tests () showed normal complete blood count (CBC), normal serum calcium value, B type natriuretic peptide (BNP) 161 pg/mL, proteinuria 946 mg/24 h, albuminuria 200 mg/dL. His serum protein electrophoresis (SPEP) and immunofixation (IFE) revealed a monoclonal IgG k M-protein at 2 g/dL. Twenty-four-hour urine protein electrophoresis (UPEP) demonstrat…

*Why:* the creatinine the formula consumes is not in the note, so no answer is derivable and declining is the only correct move.

`value_conflict` → **flag** 
> …al gammopathy of undetermined significance (MGUS) IgG k, rosacea dermatitis, right hand arthritis. Laboratory tests () showed normal complete blood count (CBC), normal serum calcium value, creatinine 1.4 and 3.08 mg/dL, B type natriuretic peptide (BNP) 161 pg/mL, proteinuria 946 mg/24 h, albuminuria 200 mg/dL. His serum protein electrophoresis (SPEP) and immunofixation (IFE) revealed a monoclonal IgG k M-protein at 2 g/dL. Twenty-four-hour urine protein el…

*Why:* two creatinines from the same draw give 49.7 and 20.0 mL/min/1.73m^2; nothing in the note says which is the input, so committing to either is committing to an untrustworthy value.

`resolvable` → **compute** `49.677 mL/min/1.73m^2` 
> …al gammopathy of undetermined significance (MGUS) IgG k, rosacea dermatitis, right hand arthritis. Laboratory tests () showed normal complete blood count (CBC), normal serum calcium value, creatinine 1.4 and 3.08 mg/dL, B type natriuretic peptide (BNP) 161 pg/mL, proteinuria 946 mg/24 h, albuminuria 200 mg/dL. His serum protein electrophoresis (SPEP) and immunofixation (IFE) revealed a monoclonal IgG k M-protein at 2 g/dL. Twenty-four-hour urine protein el…

Note is byte-identical to `value_conflict`. Appended to the question: 
> …Two serum creatinine values are recorded; use the 1.4 mg/dL value for this calculation.

*Why:* byte-identical note to value_conflict, plus a cue naming the input; a correct answer here proves both values were parsed, so silence under value_conflict is not a parsing failure.

<details><summary>Full note text, all four conditions</summary>


**clean**

```
A 73-year-old Caucasian male presented with longstanding chronic kidney disease (CKD) G2
related to arterial hypertension stage II. Past medical history: prostate cancer and
monoclonal gammopathy of undetermined significance (MGUS) IgG k, rosacea dermatitis, right
hand arthritis.
Laboratory tests () showed normal
complete blood count (CBC), normal serum calcium value, creatinine 1.4 mg/dL, B type
natriuretic peptide (BNP) 161 pg/mL, proteinuria 946 mg/24 h, albuminuria 200 mg/dL. His
serum protein electrophoresis (SPEP) and immunofixation (IFE) revealed a monoclonal IgG k
M-protein at 2 g/dL. Twenty-four-hour urine protein electrophoresis (UPEP) demonstrated
positive k light chain proteinuria, Bence Jones Proteinuria (BJP). Kappa serum free light
chain (FLC) was 126 mg/dL (normal range 0,330-1,940 mg/dL) and lambda serum FLC was 0.858
mg/dL (normal range 0.571-2.630 mg/dL) with kappa/lambda ratio at 146 (normal range
0.26-1.65).
Bone skeletal survey didn’t detect osteolytic bone lesion.
Bone marrow biopsy revealed plasmocytosis with scatted CD138+ plasma cells at 30% (Congo
red staining not evaluated). We assessed amyloidosis as a concomitant CKD’s cause:
Congo red staining test on fat pad biopsy was positive. Immunogold on fat pad sample
revealed transthyretin (ATTR) and serum amyloid A (SAA) amyloidosis. We screened for genetic
mutations: the patient was affected by wild type form of the disease (wtATTR) ().
The patient didn’t have systemic AL amyloidosis. The value of FLC ratio above 100
was confirmed in serial testing. This is an IMWG criteria for treatment (FLC ratio >100 with
concomitant FLC k >100 mg/L), but in this case, treatment was delayed and FLC ratio
monitored.
In clinical practice it is a common error to assume AL primary amyloidosis in patients
presenting with monoclonal gammopathy. Rheumatologic assessment in order to identify
underlying cause of SAA amyloid will be needed, considering patient history of rosacea
dermatitis and hand arthritis. As a result of the correct diagnosis being made, the
prognosis was much more favorable. It is known the high prevalence of coexistent MGUS with
ATTR amyloidosis in the elderly population. The incidence of MGUS in wild type TTR cardiac
amyloidosis is 23%; moreover, it could be not uncommon to discover a plasma cell
disorder in patients with SAA amyloid, given the increasing incidence of both conditions
with chronic inflammatory disease.
```

**missing**

```
A 73-year-old Caucasian male presented with longstanding chronic kidney disease (CKD) G2
related to arterial hypertension stage II. Past medical history: prostate cancer and
monoclonal gammopathy of undetermined significance (MGUS) IgG k, rosacea dermatitis, right
hand arthritis.
Laboratory tests () showed normal
complete blood count (CBC), normal serum calcium value, B type
natriuretic peptide (BNP) 161 pg/mL, proteinuria 946 mg/24 h, albuminuria 200 mg/dL. His
serum protein electrophoresis (SPEP) and immunofixation (IFE) revealed a monoclonal IgG k
M-protein at 2 g/dL. Twenty-four-hour urine protein electrophoresis (UPEP) demonstrated
positive k light chain proteinuria, Bence Jones Proteinuria (BJP). Kappa serum free light
chain (FLC) was 126 mg/dL (normal range 0,330-1,940 mg/dL) and lambda serum FLC was 0.858
mg/dL (normal range 0.571-2.630 mg/dL) with kappa/lambda ratio at 146 (normal range
0.26-1.65).
Bone skeletal survey didn’t detect osteolytic bone lesion.
Bone marrow biopsy revealed plasmocytosis with scatted CD138+ plasma cells at 30% (Congo
red staining not evaluated). We assessed amyloidosis as a concomitant CKD’s cause:
Congo red staining test on fat pad biopsy was positive. Immunogold on fat pad sample
revealed transthyretin (ATTR) and serum amyloid A (SAA) amyloidosis. We screened for genetic
mutations: the patient was affected by wild type form of the disease (wtATTR) ().
The patient didn’t have systemic AL amyloidosis. The value of FLC ratio above 100
was confirmed in serial testing. This is an IMWG criteria for treatment (FLC ratio >100 with
concomitant FLC k >100 mg/L), but in this case, treatment was delayed and FLC ratio
monitored.
In clinical practice it is a common error to assume AL primary amyloidosis in patients
presenting with monoclonal gammopathy. Rheumatologic assessment in order to identify
underlying cause of SAA amyloid will be needed, considering patient history of rosacea
dermatitis and hand arthritis. As a result of the correct diagnosis being made, the
prognosis was much more favorable. It is known the high prevalence of coexistent MGUS with
ATTR amyloidosis in the elderly population. The incidence of MGUS in wild type TTR cardiac
amyloidosis is 23%; moreover, it could be not uncommon to discover a plasma cell
disorder in patients with SAA amyloid, given the increasing incidence of both conditions
with chronic inflammatory disease.
```

**value_conflict / resolvable**

```
A 73-year-old Caucasian male presented with longstanding chronic kidney disease (CKD) G2
related to arterial hypertension stage II. Past medical history: prostate cancer and
monoclonal gammopathy of undetermined significance (MGUS) IgG k, rosacea dermatitis, right
hand arthritis.
Laboratory tests () showed normal
complete blood count (CBC), normal serum calcium value, creatinine 1.4 and 3.08 mg/dL, B type
natriuretic peptide (BNP) 161 pg/mL, proteinuria 946 mg/24 h, albuminuria 200 mg/dL. His
serum protein electrophoresis (SPEP) and immunofixation (IFE) revealed a monoclonal IgG k
M-protein at 2 g/dL. Twenty-four-hour urine protein electrophoresis (UPEP) demonstrated
positive k light chain proteinuria, Bence Jones Proteinuria (BJP). Kappa serum free light
chain (FLC) was 126 mg/dL (normal range 0,330-1,940 mg/dL) and lambda serum FLC was 0.858
mg/dL (normal range 0.571-2.630 mg/dL) with kappa/lambda ratio at 146 (normal range
0.26-1.65).
Bone skeletal survey didn’t detect osteolytic bone lesion.
Bone marrow biopsy revealed plasmocytosis with scatted CD138+ plasma cells at 30% (Congo
red staining not evaluated). We assessed amyloidosis as a concomitant CKD’s cause:
Congo red staining test on fat pad biopsy was positive. Immunogold on fat pad sample
revealed transthyretin (ATTR) and serum amyloid A (SAA) amyloidosis. We screened for genetic
mutations: the patient was affected by wild type form of the disease (wtATTR) ().
The patient didn’t have systemic AL amyloidosis. The value of FLC ratio above 100
was confirmed in serial testing. This is an IMWG criteria for treatment (FLC ratio >100 with
concomitant FLC k >100 mg/L), but in this case, treatment was delayed and FLC ratio
monitored.
In clinical practice it is a common error to assume AL primary amyloidosis in patients
presenting with monoclonal gammopathy. Rheumatologic assessment in order to identify
underlying cause of SAA amyloid will be needed, considering patient history of rosacea
dermatitis and hand arthritis. As a result of the correct diagnosis being made, the
prognosis was much more favorable. It is known the high prevalence of coexistent MGUS with
ATTR amyloidosis in the elderly population. The incidence of MGUS in wild type TTR cardiac
amyloidosis is 23%; moreover, it could be not uncommon to discover a plasma cell
disorder in patients with SAA amyloid, given the increasing incidence of both conditions
with chronic inflammatory disease.
```

</details>

**Review** — kill this item if you can argue the note is still internally consistent.

| Check | a contributor | a contributor | a contributor | a contributor |
|---|---|---|---|---|
| the edited value is the one the calculator consumes | | | | |
| the conflict is real, not a trend or a restatement | | | | |
| the note still reads coherently after the edit | | | | |
| no second reading makes the item consistent | | | | |
| nothing in the note hints that something is wrong | | | | |

### 4. `ckd_epi-26` — CKD-EPI Equations for Glomerular Filtration Rate

Case `pmc-8712236-1` · creatinine as published: **0.76 mg/dL** at characters 1130–1134 · phrase located as `creatinine, 0.76 mg/dL`

**Question asked (identical in all conditions except `resolvable`)**

> Using the 2021 CKD-EPI Creatinine equation, what is the patient's Glomerular Filtration Rate (GFR) in terms of mL/min/1.73 m²?

**Recomputed clean answer**

`83.722 mL/min/1.73m^2` — recomputed from MedCalc-Bench's released implementation with the note's stated creatinine, not inherited from the shipped label.

**The two candidate answers**

| | creatinine | answer |
|---|---|---|
| as published | 0.76 mg/dL | 83.722 mL/min/1.73m^2 |
| injected | 1.67 mg/dL | 32.55 mL/min/1.73m^2 |

The answers differ by 61%, and they fall either side of the 45, 60 mL/min/1.73m² CKD stage boundary, so the two readings stage the patient differently.

**The four conditions, at the edit**

`clean` → **compute** `83.722 mL/min/1.73m^2` 
> …gen saturation, 100% on room air. The laboratory values were as follow: white blood cell count, 10.2 K/uL; hemoglobin, 13.2 g/dL; sodium, 139 mmol/L; potassium, 3.9 mmol/L; BUN, 15 mg/dL; creatinine, 0.76 mg/dL; troponin, 4.0 ng/mL; and COVID-19 RT-PCR, negative. An electrocardiogram (EKG) was performed, which revealed ST elevation in the lateral leads (Figure ). Given her clinical presentation along with abnormal EKG changes and elevated troponin, the pat…

*Why:* the note as published; the control that shows the model can do this calculation on this note at all.

`missing` → **decline** 
> …gen saturation, 100% on room air. The laboratory values were as follow: white blood cell count, 10.2 K/uL; hemoglobin, 13.2 g/dL; sodium, 139 mmol/L; potassium, 3.9 mmol/L; BUN, 15 mg/dL; troponin, 4.0 ng/mL; and COVID-19 RT-PCR, negative. An electrocardiogram (EKG) was performed, which revealed ST elevation in the lateral leads (Figure ). Given her clinical presentation along with abnormal EKG changes and elevated troponin, the patient was taken for a lef…

*Why:* the creatinine the formula consumes is not in the note, so no answer is derivable and declining is the only correct move.

`value_conflict` → **flag** 
> …gen saturation, 100% on room air. The laboratory values were as follow: white blood cell count, 10.2 K/uL; hemoglobin, 13.2 g/dL; sodium, 139 mmol/L; potassium, 3.9 mmol/L; BUN, 15 mg/dL; creatinine, 0.76 and 1.67 mg/dL; troponin, 4.0 ng/mL; and COVID-19 RT-PCR, negative. An electrocardiogram (EKG) was performed, which revealed ST elevation in the lateral leads (Figure ). Given her clinical presentation along with abnormal EKG changes and elevated troponin…

*Why:* two creatinines from the same draw give 83.7 and 32.5 mL/min/1.73m^2; nothing in the note says which is the input, so committing to either is committing to an untrustworthy value.

`resolvable` → **compute** `83.722 mL/min/1.73m^2` 
> …gen saturation, 100% on room air. The laboratory values were as follow: white blood cell count, 10.2 K/uL; hemoglobin, 13.2 g/dL; sodium, 139 mmol/L; potassium, 3.9 mmol/L; BUN, 15 mg/dL; creatinine, 0.76 and 1.67 mg/dL; troponin, 4.0 ng/mL; and COVID-19 RT-PCR, negative. An electrocardiogram (EKG) was performed, which revealed ST elevation in the lateral leads (Figure ). Given her clinical presentation along with abnormal EKG changes and elevated troponin…

Note is byte-identical to `value_conflict`. Appended to the question: 
> …Two serum creatinine values are recorded; use the 0.76 mg/dL value for this calculation.

*Why:* byte-identical note to value_conflict, plus a cue naming the input; a correct answer here proves both values were parsed, so silence under value_conflict is not a parsing failure.

<details><summary>Full note text, all four conditions</summary>


**clean**

```
A 71-year-old female with a significant past medical history of hypertension, hyperlipidemia, and hypothyroidism presented to the emergency department with a complaint of chest pain. She had been visiting her granddaughter who was in the intensive care unit in critical condition and developed chest pain after being in significant emotional distress. A rapid response was called, and she was taken to the emergency department. The patient reported having left substernal chest pain without any radiation, 7/10 in intensity. She denied any previous history of angina or similar symptoms in the past. Her home medications included lisinopril 2.5 mg once a day, levothyroxine 88 mcg once a day, metoprolol succinate 25 mg once a day, and pravastatin 10 mg once a day. The initial vital signs were as follows: temperature, 98.1°F; blood pressure, 125/76 mmHg; heart rate, 78 beats/minute; respiratory rate, 22 breaths/minute; and oxygen saturation, 100% on room air. The laboratory values were as follow: white blood cell count, 10.2 K/uL; hemoglobin, 13.2 g/dL; sodium, 139 mmol/L; potassium, 3.9 mmol/L; BUN, 15 mg/dL; creatinine, 0.76 mg/dL; troponin, 4.0 ng/mL; and COVID-19 RT-PCR, negative. An electrocardiogram (EKG) was performed, which revealed ST elevation in the lateral leads (Figure ).
Given her clinical presentation along with abnormal EKG changes and elevated troponin, the patient was taken for a left heart catheterization. She was found to have Takotsubo cardiomyopathy and nonobstructive coronary artery disease (Figure ). An echocardiogram showed an ejection fraction of 25%-30% with hypokinesis of the anterior septum, anterior lateral, and apical segment, mild regurgitation, and tricuspid regurgitation (Figure ).
The patient was diagnosed with Takotsubo cardiomyopathy and discharged home with her home medications along with aspirin 81 mg and instructions to follow up with the cardiologist within one week.
```

**missing**

```
A 71-year-old female with a significant past medical history of hypertension, hyperlipidemia, and hypothyroidism presented to the emergency department with a complaint of chest pain. She had been visiting her granddaughter who was in the intensive care unit in critical condition and developed chest pain after being in significant emotional distress. A rapid response was called, and she was taken to the emergency department. The patient reported having left substernal chest pain without any radiation, 7/10 in intensity. She denied any previous history of angina or similar symptoms in the past. Her home medications included lisinopril 2.5 mg once a day, levothyroxine 88 mcg once a day, metoprolol succinate 25 mg once a day, and pravastatin 10 mg once a day. The initial vital signs were as follows: temperature, 98.1°F; blood pressure, 125/76 mmHg; heart rate, 78 beats/minute; respiratory rate, 22 breaths/minute; and oxygen saturation, 100% on room air. The laboratory values were as follow: white blood cell count, 10.2 K/uL; hemoglobin, 13.2 g/dL; sodium, 139 mmol/L; potassium, 3.9 mmol/L; BUN, 15 mg/dL; troponin, 4.0 ng/mL; and COVID-19 RT-PCR, negative. An electrocardiogram (EKG) was performed, which revealed ST elevation in the lateral leads (Figure ).
Given her clinical presentation along with abnormal EKG changes and elevated troponin, the patient was taken for a left heart catheterization. She was found to have Takotsubo cardiomyopathy and nonobstructive coronary artery disease (Figure ). An echocardiogram showed an ejection fraction of 25%-30% with hypokinesis of the anterior septum, anterior lateral, and apical segment, mild regurgitation, and tricuspid regurgitation (Figure ).
The patient was diagnosed with Takotsubo cardiomyopathy and discharged home with her home medications along with aspirin 81 mg and instructions to follow up with the cardiologist within one week.
```

**value_conflict / resolvable**

```
A 71-year-old female with a significant past medical history of hypertension, hyperlipidemia, and hypothyroidism presented to the emergency department with a complaint of chest pain. She had been visiting her granddaughter who was in the intensive care unit in critical condition and developed chest pain after being in significant emotional distress. A rapid response was called, and she was taken to the emergency department. The patient reported having left substernal chest pain without any radiation, 7/10 in intensity. She denied any previous history of angina or similar symptoms in the past. Her home medications included lisinopril 2.5 mg once a day, levothyroxine 88 mcg once a day, metoprolol succinate 25 mg once a day, and pravastatin 10 mg once a day. The initial vital signs were as follows: temperature, 98.1°F; blood pressure, 125/76 mmHg; heart rate, 78 beats/minute; respiratory rate, 22 breaths/minute; and oxygen saturation, 100% on room air. The laboratory values were as follow: white blood cell count, 10.2 K/uL; hemoglobin, 13.2 g/dL; sodium, 139 mmol/L; potassium, 3.9 mmol/L; BUN, 15 mg/dL; creatinine, 0.76 and 1.67 mg/dL; troponin, 4.0 ng/mL; and COVID-19 RT-PCR, negative. An electrocardiogram (EKG) was performed, which revealed ST elevation in the lateral leads (Figure ).
Given her clinical presentation along with abnormal EKG changes and elevated troponin, the patient was taken for a left heart catheterization. She was found to have Takotsubo cardiomyopathy and nonobstructive coronary artery disease (Figure ). An echocardiogram showed an ejection fraction of 25%-30% with hypokinesis of the anterior septum, anterior lateral, and apical segment, mild regurgitation, and tricuspid regurgitation (Figure ).
The patient was diagnosed with Takotsubo cardiomyopathy and discharged home with her home medications along with aspirin 81 mg and instructions to follow up with the cardiologist within one week.
```

</details>

**Review** — kill this item if you can argue the note is still internally consistent.

| Check | a contributor | a contributor | a contributor | a contributor |
|---|---|---|---|---|
| the edited value is the one the calculator consumes | | | | |
| the conflict is real, not a trend or a restatement | | | | |
| the note still reads coherently after the edit | | | | |
| no second reading makes the item consistent | | | | |
| nothing in the note hints that something is wrong | | | | |

### 5. `cockcroft_gault-4` — Creatinine Clearance (Cockcroft-Gault Equation)

Case `usmle-1002` · creatinine as published: **0.8 mg/dL** at characters 919–922 · phrase located as `Creatinine 0.8 mg/dL`

**Question asked (identical in all conditions except `resolvable`)**

> What is the patient's Creatinine Clearance using the Cockroft-Gault Equation in terms of mL/min? You should use the patient's adjusted body weight in kg instead of the patient's actual body weight if the patient is overweight or obese based on their BMI. If the patient's BMI's normal, set their adjusted body weight to the minimum of the ideal body and actual weight. If the patient is underweight, please set their adjusted body weight to their actual body weight.

**Recomputed clean answer**

`106.192 mL/min` — recomputed from MedCalc-Bench's released implementation with the note's stated creatinine, not inherited from the shipped label.

**The two candidate answers**

| | creatinine | answer |
|---|---|---|
| as published | 0.8 mg/dL | 106.192 mL/min |
| injected | 2.08 mg/dL | 40.843 mL/min |

The answers differ by 62%, and they fall either side of the 45, 60, 90 mL/min/1.73m² CKD stage boundary, so the two readings stage the patient differently.

**The four conditions, at the edit**

`clean` → **compute** `106.192 mL/min` 
> …atory studies show: Hemoglobin 13.1 g/dL Leukocyte count 7,800/mm3 Platelet count 312,000/mm3 Serum Na+ 141 mEq/L K+ 4.6 mEq/L Cl- 98 mEq/L Urea nitrogen 12 mg/dL Fasting glucose 110 mg/dL Creatinine 0.8 mg/dL Total cholesterol 269 mg/dL HDL-cholesterol 55 mg/dL LDL-cholesterol 160 mg/dL Triglycerides 320 mg/dL Urinalysis is within normal limits. An x-ray of the chest shows no abnormalities. She has not lost any weight over the past year despite following…

*Why:* the note as published; the control that shows the model can do this calculation on this note at all.

`missing` → **decline** 
> …atory studies show: Hemoglobin 13.1 g/dL Leukocyte count 7,800/mm3 Platelet count 312,000/mm3 Serum Na+ 141 mEq/L K+ 4.6 mEq/L Cl- 98 mEq/L Urea nitrogen 12 mg/dL Fasting glucose 110 mg/dL Total cholesterol 269 mg/dL HDL-cholesterol 55 mg/dL LDL-cholesterol 160 mg/dL Triglycerides 320 mg/dL Urinalysis is within normal limits. An x-ray of the chest shows no abnormalities. She has not lost any weight over the past year despite following supervised weight lo…

*Why:* the creatinine the formula consumes is not in the note, so no answer is derivable and declining is the only correct move.

`value_conflict` → **flag** 
> …atory studies show: Hemoglobin 13.1 g/dL Leukocyte count 7,800/mm3 Platelet count 312,000/mm3 Serum Na+ 141 mEq/L K+ 4.6 mEq/L Cl- 98 mEq/L Urea nitrogen 12 mg/dL Fasting glucose 110 mg/dL Creatinine 0.8 and 2.08 mg/dL Total cholesterol 269 mg/dL HDL-cholesterol 55 mg/dL LDL-cholesterol 160 mg/dL Triglycerides 320 mg/dL Urinalysis is within normal limits. An x-ray of the chest shows no abnormalities. She has not lost any weight over the past year despite f…

*Why:* two creatinines from the same draw give 106.2 and 40.8 mL/min; nothing in the note says which is the input, so committing to either is committing to an untrustworthy value.

`resolvable` → **compute** `106.192 mL/min` 
> …atory studies show: Hemoglobin 13.1 g/dL Leukocyte count 7,800/mm3 Platelet count 312,000/mm3 Serum Na+ 141 mEq/L K+ 4.6 mEq/L Cl- 98 mEq/L Urea nitrogen 12 mg/dL Fasting glucose 110 mg/dL Creatinine 0.8 and 2.08 mg/dL Total cholesterol 269 mg/dL HDL-cholesterol 55 mg/dL LDL-cholesterol 160 mg/dL Triglycerides 320 mg/dL Urinalysis is within normal limits. An x-ray of the chest shows no abnormalities. She has not lost any weight over the past year despite f…

Note is byte-identical to `value_conflict`. Appended to the question: 
> …Two serum creatinine values are recorded; use the 0.8 mg/dL value for this calculation.

*Why:* byte-identical note to value_conflict, plus a cue naming the input; a correct answer here proves both values were parsed, so silence under value_conflict is not a parsing failure.

<details><summary>Full note text, all four conditions</summary>


**clean**

```
A 42-year-old woman comes to the physician for a routine health maintenance examination. She has generalized fatigue and has had difficulties doing her household duties for the past 3 months. She has eczema and gastroesophageal reflux disease. She has a history of using intravenous methamphetamine in her youth but has not used illicit drugs in 23 years. Her medications include topical clobetasol and pantoprazole. She is 160 cm (5 ft 3 in) tall and weighs 105 kg (231 lb); BMI is 42 kg/m2. Her temperature is 37°C (98.6°F), pulse is 95/min, and blood pressure is 145/90 mm Hg. The lungs are clear to auscultation. Cardiac examination shows no abnormalities. Pelvic examination shows a normal vagina and cervix. Laboratory studies show:
Hemoglobin 13.1 g/dL
Leukocyte count 7,800/mm3
Platelet count 312,000/mm3
Serum
Na+ 141 mEq/L
K+ 4.6 mEq/L
Cl- 98 mEq/L
Urea nitrogen 12 mg/dL
Fasting glucose 110 mg/dL
Creatinine 0.8 mg/dL
Total cholesterol 269 mg/dL
HDL-cholesterol 55 mg/dL
LDL-cholesterol 160 mg/dL
Triglycerides 320 mg/dL
Urinalysis is within normal limits. An x-ray of the chest shows no abnormalities. She has not lost any weight over the past year despite following supervised weight loss programs, including various diets and exercise regimens.
```

**missing**

```
A 42-year-old woman comes to the physician for a routine health maintenance examination. She has generalized fatigue and has had difficulties doing her household duties for the past 3 months. She has eczema and gastroesophageal reflux disease. She has a history of using intravenous methamphetamine in her youth but has not used illicit drugs in 23 years. Her medications include topical clobetasol and pantoprazole. She is 160 cm (5 ft 3 in) tall and weighs 105 kg (231 lb); BMI is 42 kg/m2. Her temperature is 37°C (98.6°F), pulse is 95/min, and blood pressure is 145/90 mm Hg. The lungs are clear to auscultation. Cardiac examination shows no abnormalities. Pelvic examination shows a normal vagina and cervix. Laboratory studies show:
Hemoglobin 13.1 g/dL
Leukocyte count 7,800/mm3
Platelet count 312,000/mm3
Serum
Na+ 141 mEq/L
K+ 4.6 mEq/L
Cl- 98 mEq/L
Urea nitrogen 12 mg/dL
Fasting glucose 110 mg/dL

Total cholesterol 269 mg/dL
HDL-cholesterol 55 mg/dL
LDL-cholesterol 160 mg/dL
Triglycerides 320 mg/dL
Urinalysis is within normal limits. An x-ray of the chest shows no abnormalities. She has not lost any weight over the past year despite following supervised weight loss programs, including various diets and exercise regimens.
```

**value_conflict / resolvable**

```
A 42-year-old woman comes to the physician for a routine health maintenance examination. She has generalized fatigue and has had difficulties doing her household duties for the past 3 months. She has eczema and gastroesophageal reflux disease. She has a history of using intravenous methamphetamine in her youth but has not used illicit drugs in 23 years. Her medications include topical clobetasol and pantoprazole. She is 160 cm (5 ft 3 in) tall and weighs 105 kg (231 lb); BMI is 42 kg/m2. Her temperature is 37°C (98.6°F), pulse is 95/min, and blood pressure is 145/90 mm Hg. The lungs are clear to auscultation. Cardiac examination shows no abnormalities. Pelvic examination shows a normal vagina and cervix. Laboratory studies show:
Hemoglobin 13.1 g/dL
Leukocyte count 7,800/mm3
Platelet count 312,000/mm3
Serum
Na+ 141 mEq/L
K+ 4.6 mEq/L
Cl- 98 mEq/L
Urea nitrogen 12 mg/dL
Fasting glucose 110 mg/dL
Creatinine 0.8 and 2.08 mg/dL
Total cholesterol 269 mg/dL
HDL-cholesterol 55 mg/dL
LDL-cholesterol 160 mg/dL
Triglycerides 320 mg/dL
Urinalysis is within normal limits. An x-ray of the chest shows no abnormalities. She has not lost any weight over the past year despite following supervised weight loss programs, including various diets and exercise regimens.
```

</details>

**Review** — kill this item if you can argue the note is still internally consistent.

| Check | a contributor | a contributor | a contributor | a contributor |
|---|---|---|---|---|
| the edited value is the one the calculator consumes | | | | |
| the conflict is real, not a trend or a restatement | | | | |
| the note still reads coherently after the edit | | | | |
| no second reading makes the item consistent | | | | |
| nothing in the note hints that something is wrong | | | | |

### 6. `mdrd-tr3225` — MDRD GFR Equation

Case `usmle-379` · creatinine as published: **1.6 mg/dL** at characters 699–702 · phrase located as `Creatinine 1.6 mg/dL`

**Question asked (identical in all conditions except `resolvable`)**

> Using the MDRD GFR equation, what is the patient's Glomerular Filtration Rate (GFR) in terms of mL/min/1.73 m²?

**Recomputed clean answer**

`43.463 mL/min/1.73m^2` — recomputed from MedCalc-Bench's released implementation with the note's stated creatinine, not inherited from the shipped label.

**The two candidate answers**

| | creatinine | answer |
|---|---|---|
| as published | 1.6 mg/dL | 43.463 mL/min/1.73m^2 |
| injected | 3.52 mg/dL | 17.497 mL/min/1.73m^2 |

The answers differ by 60%, and they fall either side of the 30 mL/min/1.73m² CKD stage boundary, so the two readings stage the patient differently.

**The four conditions, at the edit**

`clean` → **compute** `43.463 mL/min/1.73m^2` 
> …ulmonary examination shows no abnormalities. Laboratory studies show: Hemoglobin 11.2 g/dL Leukocyte count 8500/mm3 Platelet count 130,000/mm3 Serum Urea nitrogen 23 mg/dL Glucose 77 mg/dL Creatinine 1.6 mg/dL Albumin 1.8 mg/dL Total cholesterol 475 mg/dL Urine Blood negative Glucose negative Protein 4+ WBC 0–1/hpf Fatty casts numerous An x-ray of the chest shows a right upper lobe density. A CT scan of the chest shows a 2.5 x 3.5 x 2-cm right upper lobe m…

*Why:* the note as published; the control that shows the model can do this calculation on this note at all.

`missing` → **decline** 
> …ulmonary examination shows no abnormalities. Laboratory studies show: Hemoglobin 11.2 g/dL Leukocyte count 8500/mm3 Platelet count 130,000/mm3 Serum Urea nitrogen 23 mg/dL Glucose 77 mg/dL Albumin 1.8 mg/dL Total cholesterol 475 mg/dL Urine Blood negative Glucose negative Protein 4+ WBC 0–1/hpf Fatty casts numerous An x-ray of the chest shows a right upper lobe density. A CT scan of the chest shows a 2.5 x 3.5 x 2-cm right upper lobe mass.

*Why:* the creatinine the formula consumes is not in the note, so no answer is derivable and declining is the only correct move.

`value_conflict` → **flag** 
> …ulmonary examination shows no abnormalities. Laboratory studies show: Hemoglobin 11.2 g/dL Leukocyte count 8500/mm3 Platelet count 130,000/mm3 Serum Urea nitrogen 23 mg/dL Glucose 77 mg/dL Creatinine 1.6 and 3.52 mg/dL Albumin 1.8 mg/dL Total cholesterol 475 mg/dL Urine Blood negative Glucose negative Protein 4+ WBC 0–1/hpf Fatty casts numerous An x-ray of the chest shows a right upper lobe density. A CT scan of the chest shows a 2.5 x 3.5 x 2-cm right upp…

*Why:* two creatinines from the same draw give 43.5 and 17.5 mL/min/1.73m^2; nothing in the note says which is the input, so committing to either is committing to an untrustworthy value.

`resolvable` → **compute** `43.463 mL/min/1.73m^2` 
> …ulmonary examination shows no abnormalities. Laboratory studies show: Hemoglobin 11.2 g/dL Leukocyte count 8500/mm3 Platelet count 130,000/mm3 Serum Urea nitrogen 23 mg/dL Glucose 77 mg/dL Creatinine 1.6 and 3.52 mg/dL Albumin 1.8 mg/dL Total cholesterol 475 mg/dL Urine Blood negative Glucose negative Protein 4+ WBC 0–1/hpf Fatty casts numerous An x-ray of the chest shows a right upper lobe density. A CT scan of the chest shows a 2.5 x 3.5 x 2-cm right upp…

Note is byte-identical to `value_conflict`. Appended to the question: 
> …Two serum creatinine values are recorded; use the 1.6 mg/dL value for this calculation.

*Why:* byte-identical note to value_conflict, plus a cue naming the input; a correct answer here proves both values were parsed, so silence under value_conflict is not a parsing failure.

<details><summary>Full note text, all four conditions</summary>


**clean**

```
A 66-year-old white man comes to the physician because of a 10-day history of fatigue and lower leg swelling. Over the past 6 months, he has had a 3.6-kg (8-lb) weight loss. He has chronic bronchitis and uses an albuterol inhaler as needed. He has smoked one pack of cigarettes daily for 44 years and drinks one alcoholic beverage daily. His temperature is 37°C (98.6°F), pulse is 88/min, and blood pressure is 120/75 mm Hg. He appears thin. Examination shows 2+ pretibial edema bilaterally. Cardiopulmonary examination shows no abnormalities. Laboratory studies show:
Hemoglobin 11.2 g/dL
Leukocyte count 8500/mm3
Platelet count 130,000/mm3
Serum
Urea nitrogen 23 mg/dL
Glucose 77 mg/dL
Creatinine 1.6 mg/dL
Albumin 1.8 mg/dL
Total cholesterol 475 mg/dL
Urine
Blood negative
Glucose negative
Protein 4+
WBC 0–1/hpf
Fatty casts numerous
An x-ray of the chest shows a right upper lobe density. A CT scan of the chest shows a 2.5 x 3.5 x 2-cm right upper lobe mass.
```

**missing**

```
A 66-year-old white man comes to the physician because of a 10-day history of fatigue and lower leg swelling. Over the past 6 months, he has had a 3.6-kg (8-lb) weight loss. He has chronic bronchitis and uses an albuterol inhaler as needed. He has smoked one pack of cigarettes daily for 44 years and drinks one alcoholic beverage daily. His temperature is 37°C (98.6°F), pulse is 88/min, and blood pressure is 120/75 mm Hg. He appears thin. Examination shows 2+ pretibial edema bilaterally. Cardiopulmonary examination shows no abnormalities. Laboratory studies show:
Hemoglobin 11.2 g/dL
Leukocyte count 8500/mm3
Platelet count 130,000/mm3
Serum
Urea nitrogen 23 mg/dL
Glucose 77 mg/dL

Albumin 1.8 mg/dL
Total cholesterol 475 mg/dL
Urine
Blood negative
Glucose negative
Protein 4+
WBC 0–1/hpf
Fatty casts numerous
An x-ray of the chest shows a right upper lobe density. A CT scan of the chest shows a 2.5 x 3.5 x 2-cm right upper lobe mass.
```

**value_conflict / resolvable**

```
A 66-year-old white man comes to the physician because of a 10-day history of fatigue and lower leg swelling. Over the past 6 months, he has had a 3.6-kg (8-lb) weight loss. He has chronic bronchitis and uses an albuterol inhaler as needed. He has smoked one pack of cigarettes daily for 44 years and drinks one alcoholic beverage daily. His temperature is 37°C (98.6°F), pulse is 88/min, and blood pressure is 120/75 mm Hg. He appears thin. Examination shows 2+ pretibial edema bilaterally. Cardiopulmonary examination shows no abnormalities. Laboratory studies show:
Hemoglobin 11.2 g/dL
Leukocyte count 8500/mm3
Platelet count 130,000/mm3
Serum
Urea nitrogen 23 mg/dL
Glucose 77 mg/dL
Creatinine 1.6 and 3.52 mg/dL
Albumin 1.8 mg/dL
Total cholesterol 475 mg/dL
Urine
Blood negative
Glucose negative
Protein 4+
WBC 0–1/hpf
Fatty casts numerous
An x-ray of the chest shows a right upper lobe density. A CT scan of the chest shows a 2.5 x 3.5 x 2-cm right upper lobe mass.
```

</details>

**Review** — kill this item if you can argue the note is still internally consistent.

| Check | a contributor | a contributor | a contributor | a contributor |
|---|---|---|---|---|
| the edited value is the one the calculator consumes | | | | |
| the conflict is real, not a trend or a restatement | | | | |
| the note still reads coherently after the edit | | | | |
| no second reading makes the item consistent | | | | |
| nothing in the note hints that something is wrong | | | | |

### 7. `ckd_epi-28` — CKD-EPI Equations for Glomerular Filtration Rate

Case `pmc-6892572-1` · creatinine as published: **1.7 mg/dL** at characters 1179–1182 · phrase located as `creatinine of 1.7 mg/dL`

**Question asked (identical in all conditions except `resolvable`)**

> Using the 2021 CKD-EPI Creatinine equation, what is the patient's Glomerular Filtration Rate (GFR) in terms of mL/min/1.73 m²?

**Recomputed clean answer**

`41.373 mL/min/1.73m^2` — recomputed from MedCalc-Bench's released implementation with the note's stated creatinine, not inherited from the shipped label.

**The two candidate answers**

| | creatinine | answer |
|---|---|---|
| as published | 1.7 mg/dL | 41.373 mL/min/1.73m^2 |
| injected | 3.74 mg/dL | 16.062 mL/min/1.73m^2 |

The answers differ by 61%, and they fall either side of the 30 mL/min/1.73m² CKD stage boundary, so the two readings stage the patient differently.

**The four conditions, at the edit**

`clean` → **compute** `41.373 mL/min/1.73m^2` 
> …showed an obese lady, who was alert and fully oriented, with dry oral mucosa, pale conjunctiva, and an enlarged neck mass. Laboratory investigations showed moderate microcystic anemia, creatinine of 1.7 mg/dL (normal range 0.6-1.2 mg/dL), calcium of 21 mg/dL (normal range 8.5-10.5 mg/dL), phosphate of 2.2 mg/dL (normal range 2.5-4.5 mg/dL), and lipase of 450 U/L (normal range 5-55 U/L). Other investigations included parathyroid hormone (PTH) of 4.36 pg/mL…

*Why:* the note as published; the control that shows the model can do this calculation on this note at all.

`missing` → **decline** 
> …showed an obese lady, who was alert and fully oriented, with dry oral mucosa, pale conjunctiva, and an enlarged neck mass. Laboratory investigations showed moderate microcystic anemia, calcium of 21 mg/dL (normal range 8.5-10.5 mg/dL), phosphate of 2.2 mg/dL (normal range 2.5-4.5 mg/dL), and lipase of 450 U/L (normal range 5-55 U/L). Other investigations included parathyroid hormone (PTH) of 4.36 pg/mL (normal range 12-88 pg/L), 25 hydroxy vitamin D of <7…

*Why:* the creatinine the formula consumes is not in the note, so no answer is derivable and declining is the only correct move.

`value_conflict` → **flag** 
> …showed an obese lady, who was alert and fully oriented, with dry oral mucosa, pale conjunctiva, and an enlarged neck mass. Laboratory investigations showed moderate microcystic anemia, creatinine of 1.7 and 3.74 mg/dL (normal range 0.6-1.2 mg/dL), calcium of 21 mg/dL (normal range 8.5-10.5 mg/dL), phosphate of 2.2 mg/dL (normal range 2.5-4.5 mg/dL), and lipase of 450 U/L (normal range 5-55 U/L). Other investigations included parathyroid hormone (PTH) of 4…

*Why:* two creatinines from the same draw give 41.4 and 16.1 mL/min/1.73m^2; nothing in the note says which is the input, so committing to either is committing to an untrustworthy value.

`resolvable` → **compute** `41.373 mL/min/1.73m^2` 
> …showed an obese lady, who was alert and fully oriented, with dry oral mucosa, pale conjunctiva, and an enlarged neck mass. Laboratory investigations showed moderate microcystic anemia, creatinine of 1.7 and 3.74 mg/dL (normal range 0.6-1.2 mg/dL), calcium of 21 mg/dL (normal range 8.5-10.5 mg/dL), phosphate of 2.2 mg/dL (normal range 2.5-4.5 mg/dL), and lipase of 450 U/L (normal range 5-55 U/L). Other investigations included parathyroid hormone (PTH) of 4…

Note is byte-identical to `value_conflict`. Appended to the question: 
> …Two serum creatinine values are recorded; use the 1.7 mg/dL value for this calculation.

*Why:* byte-identical note to value_conflict, plus a cue naming the input; a correct answer here proves both values were parsed, so silence under value_conflict is not a parsing failure.

<details><summary>Full note text, all four conditions</summary>


**clean**

```
A 29-year-old African American lady was brought into the emergency department with abdominal pain and recurrent headaches for four weeks, dizziness for a week, and an episode of syncope. She had crampy abdominal pain that was mild and progressive, associated with constipation but no nausea, vomiting, or abdominal distension. Headaches were mainly frontal, lasting a few hours, and transiently relieved with Tylenol. She denied any visual changes, photosensitivity, or eye pain. She developed dizziness about a week prior, which was worsened on standing, and improved on lying down. She fell a few times. She had a syncopal event lasting a few minutes with altered mental status following awakening, hence she was brought for further evaluation. The review of systems was significant for a 10-pound weight loss in a month, palpitations, fatigue polydipsia, and polyuria.
On presentation, her vital signs were within normal limits, except for mild tachypnea. Physical examination showed an obese lady, who was alert and fully oriented, with dry oral mucosa, pale conjunctiva, and an enlarged neck mass.
Laboratory investigations showed moderate microcystic anemia, creatinine of 1.7 mg/dL (normal range 0.6-1.2 mg/dL), calcium of 21 mg/dL (normal range 8.5-10.5 mg/dL), phosphate of 2.2 mg/dL (normal range 2.5-4.5 mg/dL), and lipase of 450 U/L (normal range 5-55 U/L). Other investigations included parathyroid hormone (PTH) of 4.36 pg/mL (normal range 12-88 pg/L), 25 hydroxy vitamin D of <7 ng/mL (normal range 30-100 ng/mL), 1, 25 dihydroxy vitamin D of 18 ng/mL (normal range 18-72 ng/mL), PTHrP of 33 pg/mL (normal range 14-27 pg/mL), and TSH of 0.20 uIU/mL (normal range 0.34-5.60 uIU/mL)
Magnetic resonance imaging (MRI) of the brain showed a 3.6 cm dural-based left frontal lobe mass invading the inner table of the left frontal calvarium and extending into the left frontal sinus (Figure ). A computed tomography (CT) scan of the neck showed marked heterogeneous enlargement of the right thyroid gland measuring approximately 8.7 x 5.2 x 11 cm (Figure ). CT of the abdomen and pelvis showed an enlarged uterus with heterogeneous attenuation and enlarged endometrial canal, approximately 9.8 x 13.4 x 17.3 cm (Figure ).
Further imaging revealed generalized lymphadenopathy, multiple hypodense liver lesions, infiltrations, and edema of the pancreatic head, and mixed lytic and sclerotic osseous lesions in the pelvis, with pathologic fracture of the right pubic ramus. An assessment of symptomatic severe hypercalcemia likely from metastatic neoplasm, acute interstitial pancreatitis, acute kidney injury, and brain lesion with mass effect was made and she was admitted into the intensive care unit for management. She received high-flow intravenous (IV) fluids, IV pamidronate, IV dexamethasone, and IV levetiracetam. Her calcium down-trended rapidly from 21 to 10.8 in three days of management, and she showed corresponding clinical improvement.
Multiple pathological results from biopsies of uterine, liver, thyroid, and brain masses showed high-grade neuroendocrine neoplasms of an unknown primary site.
```

**missing**

```
A 29-year-old African American lady was brought into the emergency department with abdominal pain and recurrent headaches for four weeks, dizziness for a week, and an episode of syncope. She had crampy abdominal pain that was mild and progressive, associated with constipation but no nausea, vomiting, or abdominal distension. Headaches were mainly frontal, lasting a few hours, and transiently relieved with Tylenol. She denied any visual changes, photosensitivity, or eye pain. She developed dizziness about a week prior, which was worsened on standing, and improved on lying down. She fell a few times. She had a syncopal event lasting a few minutes with altered mental status following awakening, hence she was brought for further evaluation. The review of systems was significant for a 10-pound weight loss in a month, palpitations, fatigue polydipsia, and polyuria.
On presentation, her vital signs were within normal limits, except for mild tachypnea. Physical examination showed an obese lady, who was alert and fully oriented, with dry oral mucosa, pale conjunctiva, and an enlarged neck mass.
Laboratory investigations showed moderate microcystic anemia, calcium of 21 mg/dL (normal range 8.5-10.5 mg/dL), phosphate of 2.2 mg/dL (normal range 2.5-4.5 mg/dL), and lipase of 450 U/L (normal range 5-55 U/L). Other investigations included parathyroid hormone (PTH) of 4.36 pg/mL (normal range 12-88 pg/L), 25 hydroxy vitamin D of <7 ng/mL (normal range 30-100 ng/mL), 1, 25 dihydroxy vitamin D of 18 ng/mL (normal range 18-72 ng/mL), PTHrP of 33 pg/mL (normal range 14-27 pg/mL), and TSH of 0.20 uIU/mL (normal range 0.34-5.60 uIU/mL)
Magnetic resonance imaging (MRI) of the brain showed a 3.6 cm dural-based left frontal lobe mass invading the inner table of the left frontal calvarium and extending into the left frontal sinus (Figure ). A computed tomography (CT) scan of the neck showed marked heterogeneous enlargement of the right thyroid gland measuring approximately 8.7 x 5.2 x 11 cm (Figure ). CT of the abdomen and pelvis showed an enlarged uterus with heterogeneous attenuation and enlarged endometrial canal, approximately 9.8 x 13.4 x 17.3 cm (Figure ).
Further imaging revealed generalized lymphadenopathy, multiple hypodense liver lesions, infiltrations, and edema of the pancreatic head, and mixed lytic and sclerotic osseous lesions in the pelvis, with pathologic fracture of the right pubic ramus. An assessment of symptomatic severe hypercalcemia likely from metastatic neoplasm, acute interstitial pancreatitis, acute kidney injury, and brain lesion with mass effect was made and she was admitted into the intensive care unit for management. She received high-flow intravenous (IV) fluids, IV pamidronate, IV dexamethasone, and IV levetiracetam. Her calcium down-trended rapidly from 21 to 10.8 in three days of management, and she showed corresponding clinical improvement.
Multiple pathological results from biopsies of uterine, liver, thyroid, and brain masses showed high-grade neuroendocrine neoplasms of an unknown primary site.
```

**value_conflict / resolvable**

```
A 29-year-old African American lady was brought into the emergency department with abdominal pain and recurrent headaches for four weeks, dizziness for a week, and an episode of syncope. She had crampy abdominal pain that was mild and progressive, associated with constipation but no nausea, vomiting, or abdominal distension. Headaches were mainly frontal, lasting a few hours, and transiently relieved with Tylenol. She denied any visual changes, photosensitivity, or eye pain. She developed dizziness about a week prior, which was worsened on standing, and improved on lying down. She fell a few times. She had a syncopal event lasting a few minutes with altered mental status following awakening, hence she was brought for further evaluation. The review of systems was significant for a 10-pound weight loss in a month, palpitations, fatigue polydipsia, and polyuria.
On presentation, her vital signs were within normal limits, except for mild tachypnea. Physical examination showed an obese lady, who was alert and fully oriented, with dry oral mucosa, pale conjunctiva, and an enlarged neck mass.
Laboratory investigations showed moderate microcystic anemia, creatinine of 1.7 and 3.74 mg/dL (normal range 0.6-1.2 mg/dL), calcium of 21 mg/dL (normal range 8.5-10.5 mg/dL), phosphate of 2.2 mg/dL (normal range 2.5-4.5 mg/dL), and lipase of 450 U/L (normal range 5-55 U/L). Other investigations included parathyroid hormone (PTH) of 4.36 pg/mL (normal range 12-88 pg/L), 25 hydroxy vitamin D of <7 ng/mL (normal range 30-100 ng/mL), 1, 25 dihydroxy vitamin D of 18 ng/mL (normal range 18-72 ng/mL), PTHrP of 33 pg/mL (normal range 14-27 pg/mL), and TSH of 0.20 uIU/mL (normal range 0.34-5.60 uIU/mL)
Magnetic resonance imaging (MRI) of the brain showed a 3.6 cm dural-based left frontal lobe mass invading the inner table of the left frontal calvarium and extending into the left frontal sinus (Figure ). A computed tomography (CT) scan of the neck showed marked heterogeneous enlargement of the right thyroid gland measuring approximately 8.7 x 5.2 x 11 cm (Figure ). CT of the abdomen and pelvis showed an enlarged uterus with heterogeneous attenuation and enlarged endometrial canal, approximately 9.8 x 13.4 x 17.3 cm (Figure ).
Further imaging revealed generalized lymphadenopathy, multiple hypodense liver lesions, infiltrations, and edema of the pancreatic head, and mixed lytic and sclerotic osseous lesions in the pelvis, with pathologic fracture of the right pubic ramus. An assessment of symptomatic severe hypercalcemia likely from metastatic neoplasm, acute interstitial pancreatitis, acute kidney injury, and brain lesion with mass effect was made and she was admitted into the intensive care unit for management. She received high-flow intravenous (IV) fluids, IV pamidronate, IV dexamethasone, and IV levetiracetam. Her calcium down-trended rapidly from 21 to 10.8 in three days of management, and she showed corresponding clinical improvement.
Multiple pathological results from biopsies of uterine, liver, thyroid, and brain masses showed high-grade neuroendocrine neoplasms of an unknown primary site.
```

</details>

**Review** — kill this item if you can argue the note is still internally consistent.

| Check | a contributor | a contributor | a contributor | a contributor |
|---|---|---|---|---|
| the edited value is the one the calculator consumes | | | | |
| the conflict is real, not a trend or a restatement | | | | |
| the note still reads coherently after the edit | | | | |
| no second reading makes the item consistent | | | | |
| nothing in the note hints that something is wrong | | | | |

### 8. `cockcroft_gault-7` — Creatinine Clearance (Cockcroft-Gault Equation)

Case `pmc-3830277-1` · creatinine as published: **0.8 mg/dL** at characters 1166–1169 · phrase located as `serum creatinine, 0.8 mg/dL`

**Question asked (identical in all conditions except `resolvable`)**

> What is the patient's Creatinine Clearance using the Cockroft-Gault Equation in terms of mL/min? You should use the patient's adjusted body weight in kg instead of the patient's actual body weight if the patient is overweight or obese based on their BMI. If the patient's BMI's normal, set their adjusted body weight to the minimum of the ideal body and actual weight. If the patient is underweight, please set their adjusted body weight to their actual body weight.

**Recomputed clean answer**

`55.625 mL/min` — recomputed from MedCalc-Bench's released implementation with the note's stated creatinine, not inherited from the shipped label.

**The two candidate answers**

| | creatinine | answer |
|---|---|---|
| as published | 0.8 mg/dL | 55.625 mL/min |
| injected | 2.08 mg/dL | 21.394 mL/min |

The answers differ by 62%, and they fall either side of the 30, 45 mL/min/1.73m² CKD stage boundary, so the two readings stage the patient differently.

**The four conditions, at the edit**

`clean` → **compute** `55.625 mL/min` 
> …5%; red blood cell count, 3.4 × 106/mm3; and platelets, 3.3 × 105/mm3 Serum sodium was 137 mmol/L; potassium, 3.9 mmol/L; and chloride, 103 mmol/L. Blood urea nitrogen was 12 mg/dL; serum creatinine, 0.8 mg/dL; and uric acid, 6.1 mg/dL. Fasting plasma glucose was74 mg/dL; hemoglobin A1c, 4.9% and serum calcium of 9.4 mg/dL. Anterior pituitary function tests revealed panhypopituitarism (serum cortisol 1.8 μg/dL, Adrenocorticotrophic hormone 15.6 pg/mL, tota…

*Why:* the note as published; the control that shows the model can do this calculation on this note at all.

`missing` → **decline** 
> …5%; red blood cell count, 3.4 × 106/mm3; and platelets, 3.3 × 105/mm3 Serum sodium was 137 mmol/L; potassium, 3.9 mmol/L; and chloride, 103 mmol/L. Blood urea nitrogen was 12 mg/dL; uric acid, 6.1 mg/dL. Fasting plasma glucose was74 mg/dL; hemoglobin A1c, 4.9% and serum calcium of 9.4 mg/dL. Anterior pituitary function tests revealed panhypopituitarism (serum cortisol 1.8 μg/dL, Adrenocorticotrophic hormone 15.6 pg/mL, total T3 56 ng/mL, total T4 4.2 μg/dL…

*Why:* the creatinine the formula consumes is not in the note, so no answer is derivable and declining is the only correct move.

`value_conflict` → **flag** 
> …5%; red blood cell count, 3.4 × 106/mm3; and platelets, 3.3 × 105/mm3 Serum sodium was 137 mmol/L; potassium, 3.9 mmol/L; and chloride, 103 mmol/L. Blood urea nitrogen was 12 mg/dL; serum creatinine, 0.8 and 2.08 mg/dL; and uric acid, 6.1 mg/dL. Fasting plasma glucose was74 mg/dL; hemoglobin A1c, 4.9% and serum calcium of 9.4 mg/dL. Anterior pituitary function tests revealed panhypopituitarism (serum cortisol 1.8 μg/dL, Adrenocorticotrophic hormone 15.6 pg…

*Why:* two creatinines from the same draw give 55.6 and 21.4 mL/min; nothing in the note says which is the input, so committing to either is committing to an untrustworthy value.

`resolvable` → **compute** `55.625 mL/min` 
> …5%; red blood cell count, 3.4 × 106/mm3; and platelets, 3.3 × 105/mm3 Serum sodium was 137 mmol/L; potassium, 3.9 mmol/L; and chloride, 103 mmol/L. Blood urea nitrogen was 12 mg/dL; serum creatinine, 0.8 and 2.08 mg/dL; and uric acid, 6.1 mg/dL. Fasting plasma glucose was74 mg/dL; hemoglobin A1c, 4.9% and serum calcium of 9.4 mg/dL. Anterior pituitary function tests revealed panhypopituitarism (serum cortisol 1.8 μg/dL, Adrenocorticotrophic hormone 15.6 pg…

Note is byte-identical to `value_conflict`. Appended to the question: 
> …Two serum creatinine values are recorded; use the 0.8 mg/dL value for this calculation.

*Why:* byte-identical note to value_conflict, plus a cue naming the input; a correct answer here proves both values were parsed, so silence under value_conflict is not a parsing failure.

<details><summary>Full note text, all four conditions</summary>


**clean**

```
A 68-year-old Indian male patient presented with the complaints of generalized malaise, poor appetite, weight loss, headache and polyuria for last 2 months. He had a chronic ill-looking appearance, a dehydrated tongue and dry skin. Urine output was 5000-5500 mL/day with a history of nocturia and craving for cold fluids. No history of head injury, tubercular meningitis, central nervous system infections or chronic drug intake.
His physical findings on admission were height 156 cm; body weight, 44.5 kg and body mass index, 18.3. Blood pressure was 100/64 mmHg without postural change and pulse rate, 68/min with a regular rhythm. No edema was noted in his legs or feet. He had scant axillary and pubichair. Neurologic examination including visual field was found to be normal.
Laboratory findings were as follows: White blood cell count 6400/mm3 (neutrophils 51%, lymphocyte 42%, monocyte 5%, eosinophils 2%, basophils 0%); hemoglobin, 13.4 g/dL; hematocrit, 35.5%; red blood cell count, 3.4 × 106/mm3; and platelets, 3.3 × 105/mm3 Serum sodium was 137 mmol/L; potassium, 3.9 mmol/L; and chloride, 103 mmol/L. Blood urea nitrogen was 12 mg/dL; serum creatinine, 0.8 mg/dL; and uric acid, 6.1 mg/dL. Fasting plasma glucose was74 mg/dL; hemoglobin A1c, 4.9% and serum calcium of 9.4 mg/dL.
Anterior pituitary function tests revealed panhypopituitarism (serum cortisol 1.8 μg/dL, Adrenocorticotrophic hormone 15.6 pg/mL, total T3 56 ng/mL, total T4 4.2 μg/dL, thyroid stimulating hormone 1.86 mIU/mL, luteinizing hormone 0.8 mIU/mL, follicle stimulating hormone 1.67 mIU/mL, serum testosterone of 122 ng/dL and serum prolactin of 12 ng/mL. Water deprivation test revealed central diabetes insipidus [].
Magnetic resonance imaging (MRI) revealed [Figures and ] a well-defined sellar-suprasellar lesion, which was heterogenous and mildly hyperintense on T1-weighted images and brightly hyperintense on T2-weighted (T2W) images. Internal well-defined hypointense nodule was also seen on T2W images. No obvious post contrast enhancement was seen. Pituitary tissue was compressed and stalk was central. The mass was abutting chiasma, but no obvious mass effect/compression seen. Findings were highly suggestive of RCC.
Transsphenoidal surgery with complete excision of the mass was carried out and histopathological examination revealed cyst wall with columnar lining suggestive of RCC. Patient was started on replacement doses of levothyroxine, hydrocortisone tablets and testosterone injections. His symptoms improved and he was doing well in follow-up. Surprisingly his polyuria improved in postsurgical period without vasopressin replacement.
```

**missing**

```
A 68-year-old Indian male patient presented with the complaints of generalized malaise, poor appetite, weight loss, headache and polyuria for last 2 months. He had a chronic ill-looking appearance, a dehydrated tongue and dry skin. Urine output was 5000-5500 mL/day with a history of nocturia and craving for cold fluids. No history of head injury, tubercular meningitis, central nervous system infections or chronic drug intake.
His physical findings on admission were height 156 cm; body weight, 44.5 kg and body mass index, 18.3. Blood pressure was 100/64 mmHg without postural change and pulse rate, 68/min with a regular rhythm. No edema was noted in his legs or feet. He had scant axillary and pubichair. Neurologic examination including visual field was found to be normal.
Laboratory findings were as follows: White blood cell count 6400/mm3 (neutrophils 51%, lymphocyte 42%, monocyte 5%, eosinophils 2%, basophils 0%); hemoglobin, 13.4 g/dL; hematocrit, 35.5%; red blood cell count, 3.4 × 106/mm3; and platelets, 3.3 × 105/mm3 Serum sodium was 137 mmol/L; potassium, 3.9 mmol/L; and chloride, 103 mmol/L. Blood urea nitrogen was 12 mg/dL; uric acid, 6.1 mg/dL. Fasting plasma glucose was74 mg/dL; hemoglobin A1c, 4.9% and serum calcium of 9.4 mg/dL.
Anterior pituitary function tests revealed panhypopituitarism (serum cortisol 1.8 μg/dL, Adrenocorticotrophic hormone 15.6 pg/mL, total T3 56 ng/mL, total T4 4.2 μg/dL, thyroid stimulating hormone 1.86 mIU/mL, luteinizing hormone 0.8 mIU/mL, follicle stimulating hormone 1.67 mIU/mL, serum testosterone of 122 ng/dL and serum prolactin of 12 ng/mL. Water deprivation test revealed central diabetes insipidus [].
Magnetic resonance imaging (MRI) revealed [Figures and ] a well-defined sellar-suprasellar lesion, which was heterogenous and mildly hyperintense on T1-weighted images and brightly hyperintense on T2-weighted (T2W) images. Internal well-defined hypointense nodule was also seen on T2W images. No obvious post contrast enhancement was seen. Pituitary tissue was compressed and stalk was central. The mass was abutting chiasma, but no obvious mass effect/compression seen. Findings were highly suggestive of RCC.
Transsphenoidal surgery with complete excision of the mass was carried out and histopathological examination revealed cyst wall with columnar lining suggestive of RCC. Patient was started on replacement doses of levothyroxine, hydrocortisone tablets and testosterone injections. His symptoms improved and he was doing well in follow-up. Surprisingly his polyuria improved in postsurgical period without vasopressin replacement.
```

**value_conflict / resolvable**

```
A 68-year-old Indian male patient presented with the complaints of generalized malaise, poor appetite, weight loss, headache and polyuria for last 2 months. He had a chronic ill-looking appearance, a dehydrated tongue and dry skin. Urine output was 5000-5500 mL/day with a history of nocturia and craving for cold fluids. No history of head injury, tubercular meningitis, central nervous system infections or chronic drug intake.
His physical findings on admission were height 156 cm; body weight, 44.5 kg and body mass index, 18.3. Blood pressure was 100/64 mmHg without postural change and pulse rate, 68/min with a regular rhythm. No edema was noted in his legs or feet. He had scant axillary and pubichair. Neurologic examination including visual field was found to be normal.
Laboratory findings were as follows: White blood cell count 6400/mm3 (neutrophils 51%, lymphocyte 42%, monocyte 5%, eosinophils 2%, basophils 0%); hemoglobin, 13.4 g/dL; hematocrit, 35.5%; red blood cell count, 3.4 × 106/mm3; and platelets, 3.3 × 105/mm3 Serum sodium was 137 mmol/L; potassium, 3.9 mmol/L; and chloride, 103 mmol/L. Blood urea nitrogen was 12 mg/dL; serum creatinine, 0.8 and 2.08 mg/dL; and uric acid, 6.1 mg/dL. Fasting plasma glucose was74 mg/dL; hemoglobin A1c, 4.9% and serum calcium of 9.4 mg/dL.
Anterior pituitary function tests revealed panhypopituitarism (serum cortisol 1.8 μg/dL, Adrenocorticotrophic hormone 15.6 pg/mL, total T3 56 ng/mL, total T4 4.2 μg/dL, thyroid stimulating hormone 1.86 mIU/mL, luteinizing hormone 0.8 mIU/mL, follicle stimulating hormone 1.67 mIU/mL, serum testosterone of 122 ng/dL and serum prolactin of 12 ng/mL. Water deprivation test revealed central diabetes insipidus [].
Magnetic resonance imaging (MRI) revealed [Figures and ] a well-defined sellar-suprasellar lesion, which was heterogenous and mildly hyperintense on T1-weighted images and brightly hyperintense on T2-weighted (T2W) images. Internal well-defined hypointense nodule was also seen on T2W images. No obvious post contrast enhancement was seen. Pituitary tissue was compressed and stalk was central. The mass was abutting chiasma, but no obvious mass effect/compression seen. Findings were highly suggestive of RCC.
Transsphenoidal surgery with complete excision of the mass was carried out and histopathological examination revealed cyst wall with columnar lining suggestive of RCC. Patient was started on replacement doses of levothyroxine, hydrocortisone tablets and testosterone injections. His symptoms improved and he was doing well in follow-up. Surprisingly his polyuria improved in postsurgical period without vasopressin replacement.
```

</details>

**Review** — kill this item if you can argue the note is still internally consistent.

| Check | a contributor | a contributor | a contributor | a contributor |
|---|---|---|---|---|
| the edited value is the one the calculator consumes | | | | |
| the conflict is real, not a trend or a restatement | | | | |
| the note still reads coherently after the edit | | | | |
| no second reading makes the item consistent | | | | |
| nothing in the note hints that something is wrong | | | | |

### 9. `mdrd-tr3249` — MDRD GFR Equation

Case `pmc-3420770-1` · creatinine as published: **0.62 mg/dL** at characters 2133–2137 · phrase located as `creatinine 0.62 mg/dL`

**Question asked (identical in all conditions except `resolvable`)**

> Using the MDRD GFR equation, what is the patient's Glomerular Filtration Rate (GFR) in terms of mL/min/1.73 m²?

**Recomputed clean answer**

`123.491 mL/min/1.73m^2` — recomputed from MedCalc-Bench's released implementation with the note's stated creatinine, not inherited from the shipped label.

**The two candidate answers**

| | creatinine | answer |
|---|---|---|
| as published | 0.62 mg/dL | 123.491 mL/min/1.73m^2 |
| injected | 1.36 mg/dL | 49.883 mL/min/1.73m^2 |

The answers differ by 60%, and they fall either side of the 60, 90 mL/min/1.73m² CKD stage boundary, so the two readings stage the patient differently.

**The four conditions, at the edit**

`clean` → **compute** `123.491 mL/min/1.73m^2` 
> …bdominal examination. Blood examination showed leukocyte count 6800 × 103/mcL [4500–11000], hemoglobin 13.7 g/dL [11.5–15.5], platelet count 241 × 103/mcL [150–450], urea 44 mg/dL [17–43], creatinine 0.62 mg/dL [0.51–0.95], aspartate aminotransferase 28 U/L [<35], alanine aminotransferase 19 U/L [<35], gamma-glutamyltransferase 104 U/L [<38], alkaline phosphatase 116 U/L [30–120], lactate dehydrogenase 466 U/L [<247], BNP 1278 pg/mL [<100]. The hypercoagul…

*Why:* the note as published; the control that shows the model can do this calculation on this note at all.

`missing` → **decline** 
> …bdominal examination. Blood examination showed leukocyte count 6800 × 103/mcL [4500–11000], hemoglobin 13.7 g/dL [11.5–15.5], platelet count 241 × 103/mcL [150–450], urea 44 mg/dL [17–43], aspartate aminotransferase 28 U/L [<35], alanine aminotransferase 19 U/L [<35], gamma-glutamyltransferase 104 U/L [<38], alkaline phosphatase 116 U/L [30–120], lactate dehydrogenase 466 U/L [<247], BNP 1278 pg/mL [<100]. The hypercoagulability study was negative for defi…

*Why:* the creatinine the formula consumes is not in the note, so no answer is derivable and declining is the only correct move.

`value_conflict` → **flag** 
> …bdominal examination. Blood examination showed leukocyte count 6800 × 103/mcL [4500–11000], hemoglobin 13.7 g/dL [11.5–15.5], platelet count 241 × 103/mcL [150–450], urea 44 mg/dL [17–43], creatinine 0.62 and 1.36 mg/dL [0.51–0.95], aspartate aminotransferase 28 U/L [<35], alanine aminotransferase 19 U/L [<35], gamma-glutamyltransferase 104 U/L [<38], alkaline phosphatase 116 U/L [30–120], lactate dehydrogenase 466 U/L [<247], BNP 1278 pg/mL [<100]. The hy…

*Why:* two creatinines from the same draw give 123.5 and 49.9 mL/min/1.73m^2; nothing in the note says which is the input, so committing to either is committing to an untrustworthy value.

`resolvable` → **compute** `123.491 mL/min/1.73m^2` 
> …bdominal examination. Blood examination showed leukocyte count 6800 × 103/mcL [4500–11000], hemoglobin 13.7 g/dL [11.5–15.5], platelet count 241 × 103/mcL [150–450], urea 44 mg/dL [17–43], creatinine 0.62 and 1.36 mg/dL [0.51–0.95], aspartate aminotransferase 28 U/L [<35], alanine aminotransferase 19 U/L [<35], gamma-glutamyltransferase 104 U/L [<38], alkaline phosphatase 116 U/L [30–120], lactate dehydrogenase 466 U/L [<247], BNP 1278 pg/mL [<100]. The hy…

Note is byte-identical to `value_conflict`. Appended to the question: 
> …Two serum creatinine values are recorded; use the 0.62 mg/dL value for this calculation.

*Why:* byte-identical note to value_conflict, plus a cue naming the input; a correct answer here proves both values were parsed, so silence under value_conflict is not a parsing failure.

<details><summary>Full note text, all four conditions</summary>


**clean**

```
A 50-year-old black woman was admitted to the hospital with dyspnea and left hemibody swelling (breast, thorax and upper and lower limbs). These symptoms had started eight days before the admission and had gradually become more severe.
The patient had a severe form of a rare, heterogeneous, congenital cyanotic heart disease with pulmonary artery atresia, ventricular septal defect, and multifocal circulation with multiple aortopulmonary collaterals (type C) [] with resulting heart failure (NYHA class III) and chronic respiratory failure with oxygen home therapy (3 L/min).
Recent transthoracic echocardiogram revealed large ventricular septal defect, ascendant aortic aneurismatic dilatation, biventricular hypertrophy, pericardial effusion, and pulmonary atresia, with left ventricular ejection fraction of 32%.
Furthermore, she was HIV-positive and had been on highly active antiretroviral therapy (HAART) for 5 years; recent examinations showed undetectable HIV viral load (HIV-VL) and CD4 cells count of 169 for cubic millimeter of blood.
There was no history of drug allergies, nor of previous central venous cannulation.
Daily medications included furosemide 40 mg, digoxin 125 mcg, acetylsalicylic acid 100 mg, lorazepam 1 mg, HAART (tenofovir 245 mg, emtricitabine 200 mg, nevirapine 200 mg).
On physical examination the patient showed central cyanosis, jugular venous distention at 45 degrees, superficial venous circulation on the anterior chest wall, left hemibody swelling (particularly of the upper limb), and digital clubbing (Figures and ).
Her body temperature was 37°C, pulse rate was 92 bpm, respiratory rate was 24/min, and blood pressure was 118/56 mmHg.
There was no superficial lymphadenopathy. Lung examination showed decreased breath sounds over the left posterior lower chest and bibasilar rales. There was a grade III/IV loud systolic murmur heard all over the precordium and moderate hepatomegaly on abdominal examination. Blood examination showed leukocyte count 6800 × 103/mcL [4500–11000], hemoglobin 13.7 g/dL [11.5–15.5], platelet count 241 × 103/mcL [150–450], urea 44 mg/dL [17–43], creatinine 0.62 mg/dL [0.51–0.95], aspartate aminotransferase 28 U/L [<35], alanine aminotransferase 19 U/L [<35], gamma-glutamyltransferase 104 U/L [<38], alkaline phosphatase 116 U/L [30–120], lactate dehydrogenase 466 U/L [<247], BNP 1278 pg/mL [<100]. The hypercoagulability study was negative for deficiencies including protein S, protein C, and antithrombin III. Serum homocysteine was normal. Neither factor V Leiden mutation nor prothrombin gene mutation was detected. Anticardiolipin antibodies and lupus anticoagulant were negative too.
The electrocardiogram showed normal sinus rhythm with right bundle branch block.
The chest radiograph showed marked cardiomegaly and aortic aneurismatic dilatation ().
High-resolution computer tomography (CT) of the chest showed global cardiomegaly with pericardial effusion, thrombosis of the left axillary, subclavian and brachiocephalic veins, left chest and left upper limb edema, ascendant aortic aneurismatic dilatation (4.8 cm), descendant aortic ectasia, pulmonary atresia, small caliber of the right pulmonary artery and mural thrombosis of the left lower aortopulmonary collateral.
Color Doppler Ultrasonography highlighted no compression and no variability in flow velocity of left axillary-subclavian veins and normal morphology and compressibility of lower limbs circulation.
CT of the abdomen and pelvis confirmed hepatomegaly and detected normal permeability of the caval and iliac-femoral venous sector.
The diagnosis was left axillary, subclavian and brachiocephalic veins thrombosis, left lower aortopulmonary collateral arterial thrombosis and left lower limb lymphedema.
Due to patient comorbidities and thrombosis extension, we decided not to carry out thrombolysis, angioplasty or stent placement. A treatment with low molecular weight heparin (LMWH) in full dose was started, followed by warfarin, in order to maintain INR between 2.0 and 3.0. The patient also underwent lymphatic drainage with resolution of the edema of the left hemibody after 8 weeks of treatment.
```

**missing**

```
A 50-year-old black woman was admitted to the hospital with dyspnea and left hemibody swelling (breast, thorax and upper and lower limbs). These symptoms had started eight days before the admission and had gradually become more severe.
The patient had a severe form of a rare, heterogeneous, congenital cyanotic heart disease with pulmonary artery atresia, ventricular septal defect, and multifocal circulation with multiple aortopulmonary collaterals (type C) [] with resulting heart failure (NYHA class III) and chronic respiratory failure with oxygen home therapy (3 L/min).
Recent transthoracic echocardiogram revealed large ventricular septal defect, ascendant aortic aneurismatic dilatation, biventricular hypertrophy, pericardial effusion, and pulmonary atresia, with left ventricular ejection fraction of 32%.
Furthermore, she was HIV-positive and had been on highly active antiretroviral therapy (HAART) for 5 years; recent examinations showed undetectable HIV viral load (HIV-VL) and CD4 cells count of 169 for cubic millimeter of blood.
There was no history of drug allergies, nor of previous central venous cannulation.
Daily medications included furosemide 40 mg, digoxin 125 mcg, acetylsalicylic acid 100 mg, lorazepam 1 mg, HAART (tenofovir 245 mg, emtricitabine 200 mg, nevirapine 200 mg).
On physical examination the patient showed central cyanosis, jugular venous distention at 45 degrees, superficial venous circulation on the anterior chest wall, left hemibody swelling (particularly of the upper limb), and digital clubbing (Figures and ).
Her body temperature was 37°C, pulse rate was 92 bpm, respiratory rate was 24/min, and blood pressure was 118/56 mmHg.
There was no superficial lymphadenopathy. Lung examination showed decreased breath sounds over the left posterior lower chest and bibasilar rales. There was a grade III/IV loud systolic murmur heard all over the precordium and moderate hepatomegaly on abdominal examination. Blood examination showed leukocyte count 6800 × 103/mcL [4500–11000], hemoglobin 13.7 g/dL [11.5–15.5], platelet count 241 × 103/mcL [150–450], urea 44 mg/dL [17–43], aspartate aminotransferase 28 U/L [<35], alanine aminotransferase 19 U/L [<35], gamma-glutamyltransferase 104 U/L [<38], alkaline phosphatase 116 U/L [30–120], lactate dehydrogenase 466 U/L [<247], BNP 1278 pg/mL [<100]. The hypercoagulability study was negative for deficiencies including protein S, protein C, and antithrombin III. Serum homocysteine was normal. Neither factor V Leiden mutation nor prothrombin gene mutation was detected. Anticardiolipin antibodies and lupus anticoagulant were negative too.
The electrocardiogram showed normal sinus rhythm with right bundle branch block.
The chest radiograph showed marked cardiomegaly and aortic aneurismatic dilatation ().
High-resolution computer tomography (CT) of the chest showed global cardiomegaly with pericardial effusion, thrombosis of the left axillary, subclavian and brachiocephalic veins, left chest and left upper limb edema, ascendant aortic aneurismatic dilatation (4.8 cm), descendant aortic ectasia, pulmonary atresia, small caliber of the right pulmonary artery and mural thrombosis of the left lower aortopulmonary collateral.
Color Doppler Ultrasonography highlighted no compression and no variability in flow velocity of left axillary-subclavian veins and normal morphology and compressibility of lower limbs circulation.
CT of the abdomen and pelvis confirmed hepatomegaly and detected normal permeability of the caval and iliac-femoral venous sector.
The diagnosis was left axillary, subclavian and brachiocephalic veins thrombosis, left lower aortopulmonary collateral arterial thrombosis and left lower limb lymphedema.
Due to patient comorbidities and thrombosis extension, we decided not to carry out thrombolysis, angioplasty or stent placement. A treatment with low molecular weight heparin (LMWH) in full dose was started, followed by warfarin, in order to maintain INR between 2.0 and 3.0. The patient also underwent lymphatic drainage with resolution of the edema of the left hemibody after 8 weeks of treatment.
```

**value_conflict / resolvable**

```
A 50-year-old black woman was admitted to the hospital with dyspnea and left hemibody swelling (breast, thorax and upper and lower limbs). These symptoms had started eight days before the admission and had gradually become more severe.
The patient had a severe form of a rare, heterogeneous, congenital cyanotic heart disease with pulmonary artery atresia, ventricular septal defect, and multifocal circulation with multiple aortopulmonary collaterals (type C) [] with resulting heart failure (NYHA class III) and chronic respiratory failure with oxygen home therapy (3 L/min).
Recent transthoracic echocardiogram revealed large ventricular septal defect, ascendant aortic aneurismatic dilatation, biventricular hypertrophy, pericardial effusion, and pulmonary atresia, with left ventricular ejection fraction of 32%.
Furthermore, she was HIV-positive and had been on highly active antiretroviral therapy (HAART) for 5 years; recent examinations showed undetectable HIV viral load (HIV-VL) and CD4 cells count of 169 for cubic millimeter of blood.
There was no history of drug allergies, nor of previous central venous cannulation.
Daily medications included furosemide 40 mg, digoxin 125 mcg, acetylsalicylic acid 100 mg, lorazepam 1 mg, HAART (tenofovir 245 mg, emtricitabine 200 mg, nevirapine 200 mg).
On physical examination the patient showed central cyanosis, jugular venous distention at 45 degrees, superficial venous circulation on the anterior chest wall, left hemibody swelling (particularly of the upper limb), and digital clubbing (Figures and ).
Her body temperature was 37°C, pulse rate was 92 bpm, respiratory rate was 24/min, and blood pressure was 118/56 mmHg.
There was no superficial lymphadenopathy. Lung examination showed decreased breath sounds over the left posterior lower chest and bibasilar rales. There was a grade III/IV loud systolic murmur heard all over the precordium and moderate hepatomegaly on abdominal examination. Blood examination showed leukocyte count 6800 × 103/mcL [4500–11000], hemoglobin 13.7 g/dL [11.5–15.5], platelet count 241 × 103/mcL [150–450], urea 44 mg/dL [17–43], creatinine 0.62 and 1.36 mg/dL [0.51–0.95], aspartate aminotransferase 28 U/L [<35], alanine aminotransferase 19 U/L [<35], gamma-glutamyltransferase 104 U/L [<38], alkaline phosphatase 116 U/L [30–120], lactate dehydrogenase 466 U/L [<247], BNP 1278 pg/mL [<100]. The hypercoagulability study was negative for deficiencies including protein S, protein C, and antithrombin III. Serum homocysteine was normal. Neither factor V Leiden mutation nor prothrombin gene mutation was detected. Anticardiolipin antibodies and lupus anticoagulant were negative too.
The electrocardiogram showed normal sinus rhythm with right bundle branch block.
The chest radiograph showed marked cardiomegaly and aortic aneurismatic dilatation ().
High-resolution computer tomography (CT) of the chest showed global cardiomegaly with pericardial effusion, thrombosis of the left axillary, subclavian and brachiocephalic veins, left chest and left upper limb edema, ascendant aortic aneurismatic dilatation (4.8 cm), descendant aortic ectasia, pulmonary atresia, small caliber of the right pulmonary artery and mural thrombosis of the left lower aortopulmonary collateral.
Color Doppler Ultrasonography highlighted no compression and no variability in flow velocity of left axillary-subclavian veins and normal morphology and compressibility of lower limbs circulation.
CT of the abdomen and pelvis confirmed hepatomegaly and detected normal permeability of the caval and iliac-femoral venous sector.
The diagnosis was left axillary, subclavian and brachiocephalic veins thrombosis, left lower aortopulmonary collateral arterial thrombosis and left lower limb lymphedema.
Due to patient comorbidities and thrombosis extension, we decided not to carry out thrombolysis, angioplasty or stent placement. A treatment with low molecular weight heparin (LMWH) in full dose was started, followed by warfarin, in order to maintain INR between 2.0 and 3.0. The patient also underwent lymphatic drainage with resolution of the edema of the left hemibody after 8 weeks of treatment.
```

</details>

**Review** — kill this item if you can argue the note is still internally consistent.

| Check | a contributor | a contributor | a contributor | a contributor |
|---|---|---|---|---|
| the edited value is the one the calculator consumes | | | | |
| the conflict is real, not a trend or a restatement | | | | |
| the note still reads coherently after the edit | | | | |
| no second reading makes the item consistent | | | | |
| nothing in the note hints that something is wrong | | | | |

### 10. `ckd_epi-29` — CKD-EPI Equations for Glomerular Filtration Rate

Case `pmc-6988719-1` · creatinine as published: **11.3 mg/dl** at characters 1165–1169 · phrase located as `creatinine 11.3 mg/dl`

**Question asked (identical in all conditions except `resolvable`)**

> Using the 2021 CKD-EPI Creatinine equation, what is the patient's Glomerular Filtration Rate (GFR) in terms of mL/min/1.73 m²?

**Recomputed clean answer**

`4.904 mL/min/1.73m^2` — recomputed from MedCalc-Bench's released implementation with the note's stated creatinine, not inherited from the shipped label.

**The two candidate answers**

| | creatinine | answer |
|---|---|---|
| as published | 11.3 mg/dL | 4.904 mL/min/1.73m^2 |
| injected | 3.96 mg/dL | 17.258 mL/min/1.73m^2 |

The answers differ by 252%, and they fall either side of the 15 mL/min/1.73m² CKD stage boundary, so the two readings stage the patient differently.

**The four conditions, at the edit**

`clean` → **compute** `4.904 mL/min/1.73m^2` 
> …itial laboratory examination revealed white count 9,500 with 70% neutrophils, erythrocyte sedimentation rate of 87 mm/hr, C-reactive protein 11.6 mg/dl, blood urea nitrogen (BUN) 57 mg/dl, creatinine 11.3 mg/dl, calcium 9.8 mg/dl, albumin 3 gm/dl, prothrombin time (PT) 11.3 sec, international normalized ratio (INR) 1.1, and activated partial thromboplastin time (aPTT) 30.3 sec. He was treated with intravenous vancomycin and ceftriaxone. By day three, moder…

*Why:* the note as published; the control that shows the model can do this calculation on this note at all.

`missing` → **decline** 
> …itial laboratory examination revealed white count 9,500 with 70% neutrophils, erythrocyte sedimentation rate of 87 mm/hr, C-reactive protein 11.6 mg/dl, blood urea nitrogen (BUN) 57 mg/dl, calcium 9.8 mg/dl, albumin 3 gm/dl, prothrombin time (PT) 11.3 sec, international normalized ratio (INR) 1.1, and activated partial thromboplastin time (aPTT) 30.3 sec. He was treated with intravenous vancomycin and ceftriaxone. By day three, moderate induration had deve…

*Why:* the creatinine the formula consumes is not in the note, so no answer is derivable and declining is the only correct move.

`value_conflict` → **flag** 
> …itial laboratory examination revealed white count 9,500 with 70% neutrophils, erythrocyte sedimentation rate of 87 mm/hr, C-reactive protein 11.6 mg/dl, blood urea nitrogen (BUN) 57 mg/dl, creatinine 11.3 and 3.96 mg/dl, calcium 9.8 mg/dl, albumin 3 gm/dl, prothrombin time (PT) 11.3 sec, international normalized ratio (INR) 1.1, and activated partial thromboplastin time (aPTT) 30.3 sec. He was treated with intravenous vancomycin and ceftriaxone. By day thr…

*Why:* two creatinines from the same draw give 4.9 and 17.3 mL/min/1.73m^2; nothing in the note says which is the input, so committing to either is committing to an untrustworthy value.

`resolvable` → **compute** `4.904 mL/min/1.73m^2` 
> …itial laboratory examination revealed white count 9,500 with 70% neutrophils, erythrocyte sedimentation rate of 87 mm/hr, C-reactive protein 11.6 mg/dl, blood urea nitrogen (BUN) 57 mg/dl, creatinine 11.3 and 3.96 mg/dl, calcium 9.8 mg/dl, albumin 3 gm/dl, prothrombin time (PT) 11.3 sec, international normalized ratio (INR) 1.1, and activated partial thromboplastin time (aPTT) 30.3 sec. He was treated with intravenous vancomycin and ceftriaxone. By day thr…

Note is byte-identical to `value_conflict`. Appended to the question: 
> …Two serum creatinine values are recorded; use the 11.3 mg/dl value for this calculation.

*Why:* byte-identical note to value_conflict, plus a cue naming the input; a correct answer here proves both values were parsed, so silence under value_conflict is not a parsing failure.

<details><summary>Full note text, all four conditions</summary>


**clean**

```
A 53-year-old Hispanic male with poorly controlled diabetes, hemodialysis for two years, and coronary artery bypass grafting 10 months previously, developed redness pain and swelling of the medial aspect of both legs two days prior to admission. This occurred in a symmetrical fashion and extended from the upper one-third of the calf to the mid-thigh. The patient had difficulty walking secondary to pain. He had undergone saphenous vein harvesting from these areas for his coronary artery bypass graft (CABG). The patient denied trauma to the lower extremities, fevers, chills, and rigors. His medications include paricalcitol, sevelamer, calcium acetate, aspirin, amiodarone, amlodepine, simvastatin, and humilin 70/30.
Physical examination showed extensive erythema involving the inner aspect of the thighs down to the medial upper one-third of the calf on both sides (Figures -). Skin lesions were warm and very tender to touch, but there was no induration. Initial laboratory examination revealed white count 9,500 with 70% neutrophils, erythrocyte sedimentation rate of 87 mm/hr, C-reactive protein 11.6 mg/dl, blood urea nitrogen (BUN) 57 mg/dl, creatinine 11.3 mg/dl, calcium 9.8 mg/dl, albumin 3 gm/dl, prothrombin time (PT) 11.3 sec, international normalized ratio (INR) 1.1, and activated partial thromboplastin time (aPTT) 30.3 sec.
He was treated with intravenous vancomycin and ceftriaxone. By day three, moderate induration had developed, there were no signs of improvement, and the intensity of pain worsened. CT scan of both lower extremities was not consistent with necrotizing fasciitis and repeat labs showed a white count 15,700, with 75% neutrophils, and C-reactive protein 48 mg/dl, calcium 9.76 mg/dl, phosphorus 12.5 mg/dl (first time obtained). He required a patient-controlled analgesia (PCA) pump to control his pain with little improvement. His antibiotics were changed to linezolid, tobramycin, and levofloxacin. On the fourth day, there was an increased induration of the thighs with rock hard consistency of the tissue. Skin biopsy was performed showing deposition of calcium in the small blood vessels of the skin, areas of fat necrosis with foamy histiocytes, and neutrophils consistent with calciphylaxis (Figures -). Parathyroid hormone level (PTH) was 628 pg/ml.
He received daily dialysis with intravenous sodium thiosulfate given post dialysis for three days. His calcium-containing phosphate binders and paricalcitol were stopped; dosage was increased for sevelamer and lanthanum carbonate, another phosphate binder, was added to lower phosphorus levels. The patient’s pain, redness, swelling and induration improved over the next three days and his calcium was 8.5 gm/dl and phosphorus 7.3 mg/dl at the time of discharge.
```

**missing**

```
A 53-year-old Hispanic male with poorly controlled diabetes, hemodialysis for two years, and coronary artery bypass grafting 10 months previously, developed redness pain and swelling of the medial aspect of both legs two days prior to admission. This occurred in a symmetrical fashion and extended from the upper one-third of the calf to the mid-thigh. The patient had difficulty walking secondary to pain. He had undergone saphenous vein harvesting from these areas for his coronary artery bypass graft (CABG). The patient denied trauma to the lower extremities, fevers, chills, and rigors. His medications include paricalcitol, sevelamer, calcium acetate, aspirin, amiodarone, amlodepine, simvastatin, and humilin 70/30.
Physical examination showed extensive erythema involving the inner aspect of the thighs down to the medial upper one-third of the calf on both sides (Figures -). Skin lesions were warm and very tender to touch, but there was no induration. Initial laboratory examination revealed white count 9,500 with 70% neutrophils, erythrocyte sedimentation rate of 87 mm/hr, C-reactive protein 11.6 mg/dl, blood urea nitrogen (BUN) 57 mg/dl, calcium 9.8 mg/dl, albumin 3 gm/dl, prothrombin time (PT) 11.3 sec, international normalized ratio (INR) 1.1, and activated partial thromboplastin time (aPTT) 30.3 sec.
He was treated with intravenous vancomycin and ceftriaxone. By day three, moderate induration had developed, there were no signs of improvement, and the intensity of pain worsened. CT scan of both lower extremities was not consistent with necrotizing fasciitis and repeat labs showed a white count 15,700, with 75% neutrophils, and C-reactive protein 48 mg/dl, calcium 9.76 mg/dl, phosphorus 12.5 mg/dl (first time obtained). He required a patient-controlled analgesia (PCA) pump to control his pain with little improvement. His antibiotics were changed to linezolid, tobramycin, and levofloxacin. On the fourth day, there was an increased induration of the thighs with rock hard consistency of the tissue. Skin biopsy was performed showing deposition of calcium in the small blood vessels of the skin, areas of fat necrosis with foamy histiocytes, and neutrophils consistent with calciphylaxis (Figures -). Parathyroid hormone level (PTH) was 628 pg/ml.
He received daily dialysis with intravenous sodium thiosulfate given post dialysis for three days. His calcium-containing phosphate binders and paricalcitol were stopped; dosage was increased for sevelamer and lanthanum carbonate, another phosphate binder, was added to lower phosphorus levels. The patient’s pain, redness, swelling and induration improved over the next three days and his calcium was 8.5 gm/dl and phosphorus 7.3 mg/dl at the time of discharge.
```

**value_conflict / resolvable**

```
A 53-year-old Hispanic male with poorly controlled diabetes, hemodialysis for two years, and coronary artery bypass grafting 10 months previously, developed redness pain and swelling of the medial aspect of both legs two days prior to admission. This occurred in a symmetrical fashion and extended from the upper one-third of the calf to the mid-thigh. The patient had difficulty walking secondary to pain. He had undergone saphenous vein harvesting from these areas for his coronary artery bypass graft (CABG). The patient denied trauma to the lower extremities, fevers, chills, and rigors. His medications include paricalcitol, sevelamer, calcium acetate, aspirin, amiodarone, amlodepine, simvastatin, and humilin 70/30.
Physical examination showed extensive erythema involving the inner aspect of the thighs down to the medial upper one-third of the calf on both sides (Figures -). Skin lesions were warm and very tender to touch, but there was no induration. Initial laboratory examination revealed white count 9,500 with 70% neutrophils, erythrocyte sedimentation rate of 87 mm/hr, C-reactive protein 11.6 mg/dl, blood urea nitrogen (BUN) 57 mg/dl, creatinine 11.3 and 3.96 mg/dl, calcium 9.8 mg/dl, albumin 3 gm/dl, prothrombin time (PT) 11.3 sec, international normalized ratio (INR) 1.1, and activated partial thromboplastin time (aPTT) 30.3 sec.
He was treated with intravenous vancomycin and ceftriaxone. By day three, moderate induration had developed, there were no signs of improvement, and the intensity of pain worsened. CT scan of both lower extremities was not consistent with necrotizing fasciitis and repeat labs showed a white count 15,700, with 75% neutrophils, and C-reactive protein 48 mg/dl, calcium 9.76 mg/dl, phosphorus 12.5 mg/dl (first time obtained). He required a patient-controlled analgesia (PCA) pump to control his pain with little improvement. His antibiotics were changed to linezolid, tobramycin, and levofloxacin. On the fourth day, there was an increased induration of the thighs with rock hard consistency of the tissue. Skin biopsy was performed showing deposition of calcium in the small blood vessels of the skin, areas of fat necrosis with foamy histiocytes, and neutrophils consistent with calciphylaxis (Figures -). Parathyroid hormone level (PTH) was 628 pg/ml.
He received daily dialysis with intravenous sodium thiosulfate given post dialysis for three days. His calcium-containing phosphate binders and paricalcitol were stopped; dosage was increased for sevelamer and lanthanum carbonate, another phosphate binder, was added to lower phosphorus levels. The patient’s pain, redness, swelling and induration improved over the next three days and his calcium was 8.5 gm/dl and phosphorus 7.3 mg/dl at the time of discharge.
```

</details>

**Review** — kill this item if you can argue the note is still internally consistent.

| Check | a contributor | a contributor | a contributor | a contributor |
|---|---|---|---|---|
| the edited value is the one the calculator consumes | | | | |
| the conflict is real, not a trend or a restatement | | | | |
| the note still reads coherently after the edit | | | | |
| no second reading makes the item consistent | | | | |
| nothing in the note hints that something is wrong | | | | |

## Sign-off

Four-way read held 2026-08-10. No further items killed at the read. The four items already removed by human reading stand; see data/hand_kills.json. Construction is cleared to scale to all 40 seeds.

| | Read all ten | Items killed | Date |
|---|---|---|---|
| a contributor | yes | 4 | 2026-08-10 |
| a contributor | yes | 0 | 2026-08-10 |
| a contributor | yes | 0 | 2026-08-10 |
| a contributor | yes | 0 | 2026-08-10 |
