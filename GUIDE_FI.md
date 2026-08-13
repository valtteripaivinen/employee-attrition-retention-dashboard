# HR Analytics & Attrition Dashboard — tarkka työohje

Tämä on toinen uusi freelancer-portfolio­projektisi. Ensimmäinen Financial Performance Dashboard osoittaa talous- ja FP&A-osaamista. Tämä projekti täydentää sitä people analytics -näkökulmalla ja sopii erityisen hyvin taustaasi, koska siinä yhdistyvät HR, johtaminen ja data-analytiikka.

Projektissa käytetään Databricksiä, PySparkia, SQL:ää, Delta-tauluja ja Power BI:tä. Lopputulos näyttää, että osaat muuttaa HR-lähdedatan analyysimalliksi, tarkistaa datan laadun, laskea vaihtuvuuden ja rakentaa liiketoimintasuosituksia ilman perusteettomia syy–seurausväitteitä.

## 1. Mitä projektissa rakennetaan

Projektin liiketoimintakysymykset ovat:

1. Mikä on kuvitteellisen henkilöstön vaihtuvuusaste?
2. Missä osastoissa ja työrooleissa havaittu vaihtuvuus on korkeampaa?
3. Miten ylityö ja työmatkustaminen liittyvät vaihtuvuuteen?
4. Miten ikä, työsuhteen pituus ja tulotaso eroavat ryhmien välillä?
5. Miten työtyytyväisyys, työympäristö ja työ–elämä-tasapaino liittyvät vaihtuvuuteen?
6. Mitkä henkilöstöryhmät ylittävät koko aineiston vaihtuvuusvertailun?
7. Millaisia HR-toimenpiteitä tulosten perusteella kannattaisi selvittää tarkemmin?

Datamalli:

- **Bronze:** lähdearvot ja latauksen metatiedot.
- **Silver:** siivotut tekstit ja oikeat numeeriset tietotyypit.
- **Gold:** HR-mittarit, luokittelut, vertailutaulut ja kuvaileva tekijäindikaattori.
- **Quality:** automaattiset tarkistukset, joiden pitää mennä läpi ennen Power BI -vientiä.

## 2. Aineiston tärkeät rajoitukset

Aineisto on IBM:n data-analytiikan harjoitteluun luotu **kuvitteellinen** aineisto. Se ei kuvaa IBM:n oikeaa henkilöstöä eikä sisällä oikeiden työntekijöiden tietoja.

Aineistossa ei ole päivämääriä. Sen vuoksi emme tee kuvitteellisia kuukausitrendejä, henkilöstöennusteita tai aikaperusteista vaihtuvuuskehitystä.

`MonthlyIncome`, `DailyRate`, `HourlyRate` ja `MonthlyRate` eivät sisällä dokumentoitua valuuttaa. Power BI:ssä niihin ei lisätä euron tai dollarin symbolia.

Projektin kuvaileva tekijäindikaattori ei ole koneoppimis- tai ennustemalli. Se laskee yhteen seitsemän läpinäkyvää ehtoa ja sitä käytetään vain aineiston ryhmätason havainnollistamiseen. Sitä ei saa esitellä työntekijän lähtötodennäköisyytenä tai käyttää oikeisiin työsuhdepäätöksiin.

## 3. Lataa aineisto

Aineisto: **IBM HR Analytics Employee Attrition & Performance**.

- Kaggle-sivu: https://www.kaggle.com/datasets/pavansubhasht/ibm-hr-analytics-attrition-dataset
- Suora ZIP-lataus: https://www.kaggle.com/api/v1/datasets/download/pavansubhasht/ibm-hr-analytics-attrition-dataset

Toimi näin:

1. Avaa suora ZIP-latauslinkki.
2. Jos selain kysyy lupaa lataamiseen, hyväksy se.
3. Avaa Macin **Lataukset/Downloads**-kansio.
4. Pura ladattu ZIP-tiedosto kaksoisklikkaamalla sitä.
5. Tarkista, että puretusta kansiosta löytyy täsmälleen:

```text
WA_Fn-UseC_-HR-Employee-Attrition.csv
```

Älä muuta CSV:n sarakenimiä tai sisältöä. Jos haluat lyhentää tiedoston nimeä, myös notebookin `file_name`-widget pitää muuttaa vastaamaan uutta nimeä. Helpoin ratkaisu on säilyttää alkuperäinen nimi.

Odotettu lähderakenne:

| Tarkistus | Odotettu arvo |
|---|---:|
| Datarivit | 1 470 |
| Sarakkeet | 35 |
| Puuttuvat arvot | 0 |
| Tarkat duplikaatit | 0 |
| Yksilölliset EmployeeNumber-arvot | 1 470 |

## 4. Tuo notebookit Databricksiin

### 4.1 Luo projektikansio

1. Kirjaudu Databricks Free Editioniin.
2. Valitse vasemmalta **Workspace**.
3. Avaa oma käyttäjäkansiosi.
4. Valitse **Create → Folder**.
5. Anna nimeksi:

```text
hr-analytics-dashboard
```

### 4.2 Tuo notebookit

Tuo projektipaketin `notebooks`-kansiosta nämä tiedostot:

1. `01_load_and_clean.py`
2. `02_feature_engineering_and_metrics.py`
3. `03_quality_checks_and_sql.py`
4. `04_export_for_power_bi.py`

Jokaiselle tiedostolle:

1. Avaa Databricksissä luomasi kansio.
2. Valitse **Import**.
3. Valitse **File**.
4. Valitse kyseinen `.py`-tiedosto.
5. Vahvista tuonti.

Tiedostot ovat Databricks Source -notebookeja. Databricks jakaa ne automaattisesti soluihin `# COMMAND ----------` -merkintöjen kohdalta.

## 5. Notebook 01 — lataa, siivoa ja tyypitä data

### 5.1 Tarkista widgetit

Notebookin yläreunan oletusarvot ovat:

- `catalog = workspace`
- `schema = hr_portfolio`
- `volume = source_files`
- `file_name = WA_Fn-UseC_-HR-Employee-Attrition.csv`

Pidä nämä arvot, jos käytit ensimmäisessäkin projektissa `workspace`-catalogia.

### 5.2 Luo skeema ja Volume

1. Avaa `01_load_and_clean`.
2. Liitä notebook compute-resurssiin, jos Databricks pyytää sitä.
3. Suorita ensimmäinen Python-solu, joka luo widgetit.
4. Suorita seuraava solu, joka sisältää `CREATE SCHEMA` ja `CREATE VOLUME`.
5. Ensimmäisellä suorituksella saat todennäköisesti `FileNotFoundError`-virheen. Tämä on odotettu: Volume on luotu mutta CSV:tä ei ole vielä ladattu.

Oletuspolku on:

```text
/Volumes/workspace/hr_portfolio/source_files/
```

### 5.3 Lataa CSV Volumeen

1. Avaa Databricksin vasemmalta **Catalog**.
2. Avaa `workspace`.
3. Avaa skeema `hr_portfolio`.
4. Avaa **Volumes → source_files**.
5. Valitse **Upload files** tai **Upload to this volume**.
6. Valitse koneeltasi:

```text
WA_Fn-UseC_-HR-Employee-Attrition.csv
```

7. Odota latauksen valmistumista.

### 5.4 Suorita notebook kokonaan

1. Palaa notebookiin 01.
2. Valitse **Run all**.
3. Odota, että jokainen solu valmistuu.

Notebook tekee seuraavat asiat:

- lukee CSV:n ensin tekstinä;
- poistaa mahdollisen BOM-erikoismerkin ensimmäisestä sarakenimestä;
- muuttaa sarakkeet `snake_case`-muotoon;
- tarkistaa, että kaikki 35 saraketta löytyvät;
- tallentaa alkuperäisen version Bronze-tauluksi;
- siistii tekstiarvot;
- muuttaa 26 numeerista saraketta kokonaisluvuiksi;
- tallentaa siivotun Silver-taulun.

Notebook luo:

```text
workspace.hr_portfolio.bronze_hr_employee_raw
workspace.hr_portfolio.silver_hr_employees
```

Onnistuneen ajon yhteenvedossa pitäisi näkyä:

| Mittari | Odotettu arvo |
|---|---:|
| Employee rows | 1 470 |
| Unique employee numbers | 1 470 |
| Attritions | 237 |
| Average age | 36,92 |
| Average monthly income | 6 502,93 |

## 6. Notebook 02 — HR-mittarit ja ryhmävertailut

1. Avaa `02_feature_engineering_and_metrics`.
2. Tarkista `catalog = workspace` ja `schema = hr_portfolio`.
3. Valitse **Run all**.

Notebook luo seuraavat kentät:

- `attrition_flag` ja `retained_flag`;
- ikä-, työsuhde-, tulo- ja etäisyysluokat;
- koulutus- ja tyytyväisyysasteikkojen tekstiselitteet;
- työ–elämä-tasapainon tekstiselitteen;
- ylennystä odottaneen ajan luokan;
- seitsemän läpinäkyvää tekijälippua;
- `descriptive_factor_count`-luvun 0–7;
- `descriptive_factor_band`-luokan Low, Moderate tai Elevated.

Tekijäindikaattorin seitsemän ehtoa ovat:

1. ylityö = Yes;
2. työmatkustus = Travel_Frequently;
3. työtyytyväisyys 1–2;
4. työ–elämä-tasapaino 1–2;
5. työympäristötyytyväisyys 1–2;
6. stock option level = 0;
7. distance from home yli 10.

Indikaattori on tarkoituksella yksinkertainen ja täysin selitettävä. Se ei sisällä yksilön lähtötodennäköisyyttä.

Notebook laskee myös `attrition_lift`-mittarin:

```text
ryhmän vaihtuvuusaste / koko aineiston vaihtuvuusaste
```

Esimerkiksi lift 1,50 tarkoittaa, että ryhmän havaittu vaihtuvuusaste on 1,5-kertainen koko aineistoon verrattuna. Se osoittaa yhteyden aineistossa, ei todista syytä.

Notebook luo:

- `gold_hr_employee_analytics`
- `gold_hr_workforce_summary`
- `gold_hr_attrition_drivers`
- `gold_hr_department_summary`
- `gold_hr_job_role_summary`

Odotetut päätulokset:

| Mittari | Odotettu arvo |
|---|---:|
| Headcount | 1 470 |
| Attritions | 237 |
| Retained employees | 1 233 |
| Attrition rate | 16,12 % |
| Average age | 36,92 |
| Average monthly income | 6 502,93 |
| Average years at company | 7,01 |

## 7. Notebook 03 — laatutarkistukset ja SQL

1. Avaa `03_quality_checks_and_sql`.
2. Tarkista catalog ja schema.
3. Valitse **Run all**.
4. Etsi tulostus:

```text
MODEL STATUS: PASS
```

Notebook tarkistaa muun muassa:

- rivimäärä on 1 470;
- Silver- ja Gold-rivimäärät täsmäävät;
- vaaditut kentät eivät ole tyhjiä;
- jokainen `employee_number` on yksilöllinen;
- duplikaatteja ei ole;
- Attrition ja OverTime sisältävät vain arvot Yes/No;
- tyytyväisyysasteikot ovat välillä 1–4;
- työkokemuksen aikakentät ovat keskenään loogisia;
- lähteen vakiosarakkeet ovat oikein;
- Attrition=Yes-rivejä on 237;
- tekijäindikaattori on merkitty ei-ennustavaksi;
- vertailutaulu on syntynyt.

Jos status on `FAIL`, älä jatka Power BI -vientiin. Katso epäonnistuneesta tarkistusrivistä `where_to_fix` ja korjaa ongelma kyseisessä notebookissa. Älä poista laatutarkistusta vain saadaksesi PASS-tuloksen.

Laatutarkistusten jälkeen notebook näyttää SQL-analyysit:

1. henkilöstön KPI:t;
2. osastot;
3. työroolit;
4. ylityön ja työmatkustamisen;
5. ikä- ja työsuhdekohortit;
6. tulotason ja urakehityksen;
7. henkilöstökokemuksen;
8. etäisyyden ja stock option -tason;
9. kuvailevat tekijäluokat;
10. korkeimmat ryhmätason attrition lift -luvut;
11. lähteen lopullisen täsmäytyksen.

Erillinen `sql/hr_analysis.sql` sisältää vastaavat kyselyt Databricks SQL Editorissa käytettäviksi.

## 8. Notebook 04 — tee Power BI -CSV:t

1. Varmista, että notebook 03 antoi `MODEL STATUS: PASS`.
2. Avaa `04_export_for_power_bi`.
3. Pidä arvot:
   - `catalog = workspace`
   - `schema = hr_portfolio`
   - `export_volume = power_bi_exports`
4. Valitse **Run all**.

Notebook luo:

```text
/Volumes/workspace/hr_portfolio/power_bi_exports/
```

ja neljä tiedostoa:

- `hr_employee_analytics.csv`
- `hr_attrition_drivers.csv`
- `hr_department_summary.csv`
- `hr_job_role_summary.csv`

### Lataa tiedostot Macille

1. Avaa Databricksistä **Catalog**.
2. Avaa `workspace → hr_portfolio → Volumes → power_bi_exports`.
3. Valitse CSV-tiedostot.
4. Paina **Download**.
5. Tiedostot tallentuvat Macin Downloads-kansioon.

## 9. Tuo CSV:t Power BI:hin

1. Avaa Power BI Desktop.
2. Valitse **Get Data → Text/CSV**.
3. Tuo kaikki neljä CSV:tä.
4. Nimeä taulut:

| CSV | Power BI -nimi |
|---|---|
| `hr_employee_analytics` | `HR` |
| `hr_attrition_drivers` | `Drivers` |
| `hr_department_summary` | `Department Summary` |
| `hr_job_role_summary` | `Job Role Summary` |

5. Avaa **Transform data**.
6. Tarkista tietotyypit:
   - `employee_number` ja muut laskurit = Whole number;
   - income-, rate- ja average-kentät = Decimal number tai Whole number sisällön mukaan;
   - attrition rate-, overtime rate- ja lift-kentät = Decimal number;
   - kategoriat = Text;
   - `descriptive_indicator_is_predictive` = True/False.
7. Valitse **Close & Apply**.

Älä luo suhdetta `HR`- ja `Drivers`-taulujen välille. Drivers-taulu sisältää saman henkilöstön useaan kertaan eri ulottuvuuksien yhteenvetoina. Jos niiden välille luodaan suhde, luvut voivat mennä väärin.

Department Summary- ja Job Role Summary -taulut ovat vapaaehtoisia tarkistus- ja yhteenvetotauluja. Varsinaiset dashboardit voidaan rakentaa pääasiassa HR-taulusta.

## 10. Luo DAX-mittarit

1. Avaa projektipaketista `power_bi/measures.dax`.
2. Valitse Power BI:ssä HR-taulu.
3. Valitse **Modeling → New measure**.
4. Kopioi yksi mittari kerrallaan.
5. Toista, kunnes kaikki HR-mittarit on luotu.
6. Valitse Drivers-taulu ja luo lopuksi Drivers-mittarit.

Tärkeimmät mittarit:

- Headcount
- Attritions
- Retained Employees
- Attrition Rate %
- Retention Rate %
- Average Age
- Average Monthly Income
- Average Years at Company
- Overtime Rate %
- Overtime Attrition Rate %
- Non-Overtime Attrition Rate %
- Overtime Attrition Gap
- Driver Attrition Lift

Muotoile:

- attrition-, retention- ja overtime-luvut prosenttimuotoon yhdellä desimaalilla;
- headcount kokonaisluvuksi;
- keskiarvot yhdellä tai kahdella desimaalilla;
- monthly income ilman valuuttasymbolia;
- factor count kokonaisluvuksi.

## 11. Rakenna neljä Power BI -sivua

Tarkka visuaalilista löytyy `power_bi/dashboard_plan.md`-tiedostosta.

### Sivu 1 — Workforce Overview

Lisää:

- slicerit Department, Job Role, Gender ja Age Band;
- KPI-kortit Headcount, Attritions, Attrition Rate %, Average Age ja Average Years at Company;
- donut chart henkilöstöstä osastoittain;
- bar chart työroolien henkilöstömääristä;
- clustered bar chart osastojen headcountista ja attritioneista;
- Department × Job Role -matriisi.

### Sivu 2 — Attrition Drivers

Lisää:

- KPI-kortit Attrition Rate %, Overtime Attrition Rate %, Non-Overtime Attrition Rate % ja Overtime Attrition Gap;
- vaihtuvuusaste työrooleittain;
- vaihtuvuusaste ylityön mukaan;
- vaihtuvuusaste työmatkustamisen mukaan;
- Age Band × Tenure Band -matriisi ja prosenttien conditional formatting;
- erillinen Drivers-taulun attrition lift -kaavio.

Drivers-kaaviossa:

1. Axis = `Drivers[category]`.
2. Values = `Driver Attrition Lift`.
3. Slicer = `Drivers[dimension]`.
4. Visual-level filter: `Drivers[headcount]` on vähintään 25.
5. Lisää `headcount`, `attritions` ja `attrition_rate` tooltippiin.

### Sivu 3 — Employee Experience

Lisää:

- Average Job Satisfaction;
- Average Environment Satisfaction;
- Average Work-Life Balance;
- Average Job Involvement;
- vaihtuvuusaste työtyytyväisyysluokittain;
- vaihtuvuusaste work-life balance -luokittain;
- vaihtuvuusaste environment satisfaction -luokittain;
- tyytyväisyys × work-life balance -matriisi;
- henkilöstömäärä kuvailevan factor bandin mukaan.

Lisää sivulle näkyvä teksti:

> The descriptive factor band is a transparent aggregate indicator, not an individual attrition prediction.

### Sivu 4 — Compensation & Career

Lisää:

- Average Monthly Income;
- Average Salary Hike %;
- Average Years Since Promotion;
- Average Years at Company;
- keskimääräinen monthly income työrooleittain;
- keskimääräinen monthly income job levelin mukaan;
- scatter chart: income vs attrition rate työrooleittain;
- vaihtuvuusaste income bandin mukaan;
- vaihtuvuusaste promotion wait bandin mukaan;
- työrooli × job level -matriisi.

## 12. Odotetut liiketoimintahavainnot

Varmista jokainen luku omasta dashboardistasi ennen kuin kirjoitat sen GitHubiin. Koko aineistossa pitäisi näkyä ainakin:

- 1 470 kuvitteellista työntekijää;
- 237 Attrition=Yes-riviä;
- kokonaisvaihtuvuus noin 16,12 %;
- Sales-osaston vaihtuvuus noin 20,63 %;
- Human Resources -osaston vaihtuvuus noin 19,05 %;
- Research & Development -osaston vaihtuvuus noin 13,84 %;
- Sales Representative -roolin vaihtuvuus noin 39,76 %, mutta ryhmässä on vain 83 henkilöä;
- Laboratory Technician -roolin vaihtuvuus noin 23,94 %;
- ylityötä tekevien vaihtuvuus noin 30,53 % ja muiden noin 10,44 %;
- usein matkustavien vaihtuvuus noin 24,91 % ja ei-matkustavien noin 8,00 %;
- matalimman työtyytyväisyysluokan vaihtuvuus noin 22,84 %;
- work-life balance -arvon 1 vaihtuvuus noin 31,25 %, mutta ryhmässä on vain 80 henkilöä;
- stock option level 0 -ryhmän vaihtuvuus noin 24,41 %.

Kuvailevan tekijäindikaattorin tulokset:

| Factor band | Headcount | Attritions | Havaittu attrition rate |
|---|---:|---:|---:|
| Low | 862 | 66 | 7,66 % |
| Moderate | 553 | 138 | 24,95 % |
| Elevated | 55 | 33 | 60,00 % |

Tätä ei saa tulkita mallin 60 prosentin ennusteeksi. Se on saman kuvitteellisen aineiston sisäinen jälkikäteinen ryhmävertailu, jolla havainnollistetaan useiden samanaikaisten tekijöiden kasaantumista.

## 13. Kirjoita vastuulliset suositukset

Hyvä suositus sisältää havainnon, rajauksen ja ehdotetun jatkotoimenpiteen.

Esimerkki:

> Employees recorded as working overtime had a substantially higher observed attrition rate than employees without overtime. Because the dataset is fictional and cross-sectional, this does not establish that overtime causes attrition. A real organization should investigate overtime volume, workload, scheduling, manager practices, and employee feedback before designing a targeted workload intervention.

Mahdollisia toimenpide-ehdotuksia:

1. selvitä ylityön syyt rooli- ja osastotasolla;
2. tarkista usein matkustavien työnkuvat ja palautumisen tuki;
3. tee tarkempi laadullinen selvitys Sales Representative- ja Laboratory Technician -rooleista;
4. tutki matalan työtyytyväisyyden taustatekijöitä henkilöstökyselyllä;
5. arvioi urakehityksen, stock option -tason ja palkkarakenteen johdonmukaisuutta;
6. seuraa oikeassa organisaatiossa vaihtuvuutta ajallisesti ja huomioi ryhmäkoot.

Älä suosittele tietyn sukupuolen, iän tai siviilisäädyn työntekijöiden erilaista kohtelua. Näitä tietoja voidaan käyttää vain ryhmätason oikeudenmukaisuuden seurantaan ja mahdollisten erojen tutkimiseen.

## 14. Tee projektista GitHub-julkaisu

Kun dashboard on valmis:

1. Ota kuva jokaisesta neljästä Power BI -sivusta.
2. Ota kuva Databricksin `MODEL STATUS: PASS` -tuloksesta.
3. Ota kuva SQL-kyselystä, joka vertaa ylityötä tai työrooleja.
4. Tallenna Power BI -tiedosto nimellä:

```text
hr-analytics-attrition-dashboard.pbix
```

5. Lisää GitHub-repoon projektipaketin tiedostot.
6. Älä julkaise Databricks-tunnuksia, tokeneita tai yhteystietoja.
7. Tarkista Kaggle-ehdot ennen raaka-CSV:n julkaisemista. Turvallisin tapa on jättää CSV reposta pois ja lisätä sen sijaan latauslinkki.
8. Lisää README:hen 3–5 tärkeintä havaintoa ja 2–3 vastuullista suositusta.

Portfolio­kuvaus englanniksi:

> Built an end-to-end HR analytics and attrition dashboard using Databricks, PySpark, SQL, Delta Lake, automated data-quality checks, and Power BI. Analyzed aggregate workforce patterns across departments, job roles, overtime, travel, employee experience, compensation, and career development using a fictional IBM-created practice dataset. Documented analytical limitations and responsible-use considerations throughout the project.

## 15. Tavallisimmat virheet

### `FileNotFoundError`

CSV ei ole widgettien osoittamassa Volumessa. Tarkista:

```text
/Volumes/workspace/hr_portfolio/source_files/WA_Fn-UseC_-HR-Employee-Attrition.csv
```

### `Source structure mismatch`

Käytit eri CSV:tä tai tiedoston sarakkeita on muutettu. Lataa alkuperäinen Kaggle-tiedosto uudelleen.

### `TABLE_OR_VIEW_NOT_FOUND`

Notebookit on ajettu väärässä järjestyksessä tai widgettien catalog/schema-arvot eroavat. Aja 01 → 02 → 03 → 04 ja käytä kaikissa samoja arvoja.

### `MODEL STATUS: FAIL`

Avaa epäonnistunut tarkistusrivi ja katso `where_to_fix`. Varmista ensimmäiseksi, että lähdetiedostossa on 1 470 riviä eikä sitä ole muokattu Excelissä.

### Power BI laskee Headcountin väärin

Käytä mittaria `DISTINCTCOUNT(HR[employee_number])`, älä raakaa Count-toimintoa.

### Power BI:n Drivers-luvut ovat liian suuria

Poista HR- ja Drivers-taulujen välinen suhde. Drivers sisältää saman henkilöstön useana eri yhteenvetona.

### Income-kentässä näkyy euro- tai dollarisymboli

Poista valuuttamuotoilu. Lähde ei kerro valuuttaa.

### En löydä CSV-tiedostoja

Suorita notebook 04 ja avaa:

```text
Catalog → workspace → hr_portfolio → Volumes → power_bi_exports
```

## 16. Valmis-määritelmä

Projekti on valmis, kun:

- notebookit 01–04 toimivat oikeassa järjestyksessä;
- laatustatus on PASS;
- kaikki kahdeksan Delta-taulua löytyvät Catalogista;
- neljä Power BI -CSV:tä on ladattu;
- Power BI:ssä on neljä viimeisteltyä raporttisivua;
- datasetin kuvitteellisuus näkyy dashboardissa ja README:ssä;
- aikasarjoja tai valuuttaa ei ole keksitty;
- factor band on merkitty ei-ennustavaksi;
- GitHub sisältää README:n, notebookit, SQL:n, DAX-mittarit ja dashboard-kuvat;
- johtopäätökset huomioivat ryhmäkoon ja erottavat yhteyden syy–seuraussuhteesta.

