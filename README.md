
<h1 align="center">
  <br>
  <a><img src="./logo_no_bg.png"
  width="400"></a>
  <br>
  Methods Validation App
<br>
</h1>
<h2 align="center">MVA WILL BE PUBLISHED SOON.</h2>
<h4 align="center">Analytical method validation software written in Python.</h4>

<p align="center">
  <a href="#key-features">Key Features</a> •
  <a href="#web-app">Web-app</a> •
  <a href="#run-locally">Run Locally</a> •
  <a href="#run-on-a-server">Run on a Server</a> •
  <a href="#datasets">Datasets</a> •
  <a href="#code-structure-project">Code Structure Project</a> •
  <br>
  <a href="#download">Download</a> •
  <a href="#credits">Credits</a> •
  <a href="#related">Related</a> •
  <a href="#how-to-cite-us">How To Cite Us</a> 
  <br>
  <a href="#license">License</a>
</p>


## Key Features

* Fast and easy - Change your approach to validation protocols!
* Modular
  - Each page can be independently explored
* Free to use  
* Import your data
	- .xls/.xlsx, .csv, .txt format allowed
* Calibration study
* Hubaux and Vos method for LOD calculation
* Precision
* Accuracy
* Matrix effect
* Recovery

## Web-app
MVA (Version 1.0) is now freely available at [mva.databloom.it](https://mva.databloom.it/).

## Run Locally

MVA is developed and tested on **Python 3.10**. The pinned dependencies install on 3.9 – 3.11;
`numpy==1.23.2`, `pandas==1.5.3` and `matplotlib==3.7.1` publish no wheels for 3.12 or newer, so
`pip install` will fail there.

### 1. Clone the repository

```bash
git clone https://github.com/giovannisolarino/Methods-Validation-App-Web.git
cd Methods-Validation-App-Web
```

### 2. Create a virtual environment with Python 3.10

<details open>
<summary><b>Windows</b></summary>

```powershell
py -3.10 -m venv .venv
.venv\Scripts\activate
```
</details>

<details>
<summary><b>macOS / Linux</b></summary>

```bash
python3.10 -m venv .venv
source .venv/bin/activate
```
</details>

Check you got the right interpreter:

```bash
python --version      # Python 3.10.x
```

### 3. Install the dependencies

```bash
pip install -r requirements.txt
```

### 4. Launch

> **Run `main.py` from inside the `MVA/` folder.** Static files, the favicon and the
> `.nicegui/` working directory are all resolved relative to the current directory, so
> launching from the repository root fails at start-up.

```bash
cd MVA
python main.py
```

Then open **<http://localhost:8080>** in your browser. Stop the server with `Ctrl+C`.

That is all a local run needs: no configuration, no environment variables. MVA starts in local
mode by default and clears any dataset left over from your previous session, so every launch
begins on a clean slate.

### Notes

* `ui.run(host="0.0.0.0")` binds every network interface, so the app is reachable from other
  machines on your network. Change it to `host="127.0.0.1"` to keep it to your own machine.
* A `.nicegui/` folder is created inside `MVA/` on first launch. It holds the session storage.
  It is safe to delete when the app is not running.
* No dataset of your own? Press **Load example dataset** on the *Import data* page to load a
  bundled amphetamine calibration curve (5 levels, 3 curves on each of 3 days, ISTD at
  100 ppb), or download the blank template from the **Info** button.

## Run on a Server

The same code serves several users at once. Each browser session keeps its own dataset, keyed
by a signed session cookie, and users never see each other's data.

Server mode is opt-in through two environment variables:

| Variable | Required | Purpose |
|---|---|---|
| `MVA_SERVER` | yes, set to `1` | Switches MVA to server mode. |
| `MVA_STORAGE_SECRET` | yes | Signs the session cookie that keys each user's dataset. |

Generate a secret once and keep it private:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

Then launch:

<details open>
<summary><b>Linux / macOS</b></summary>

```bash
cd MVA
export MVA_SERVER=1
export MVA_STORAGE_SECRET="<paste the generated secret>"
python main.py
```
</details>

<details>
<summary><b>Windows (PowerShell)</b></summary>

```powershell
cd MVA
$env:MVA_SERVER = "1"
$env:MVA_STORAGE_SECRET = "<paste the generated secret>"
python main.py
```
</details>

MVA refuses to start in server mode without `MVA_STORAGE_SECRET`. This is deliberate: the
secret signs the cookie that identifies each user, so a shared or guessable value would let a
forged cookie read somebody else's dataset.

### What differs between the two modes

| | Local (default) | Server (`MVA_SERVER=1`) |
|---|---|---|
| Storage secret | Built-in development value | **You must** supply `MVA_STORAGE_SECRET` |
| Sessions on restart | Cleared, so each launch starts empty | Preserved, so a restart does not sign everyone out |
| Concurrent users | One | Many, each isolated |

In server mode users clear their own data with the **Clear memory** switch on the *Import data*
page. Restarting the process is not a way to reset a single user, since it would leave every
other session untouched.

## Datasets
Inside the [dataset](./dataset/) folder you can find three datasets to explore how MVA works. Examples on how to use them is provided in the [User Guide](./User_Manual_MVA_1_0.pdf).

## Code Structure Project
```
Methods-Validation-App-Web/
├─ MVA/
│  ├─ theme.py                       # Shared theme across pages
|  ├─ menu.py                        # Shared menu across pages
|  ├─ home_page.py
|  ├─ all_pages.py
|  ├─ main.py                        # Main entry, local vs server mode
|  ├─ test_isolation.py              # Checks the pages keep no shared state
│  ├─ pages/                         # NiceGUI pages (UI only)
│  │  ├─ import_data.py
│  │  ├─ linearity.py
│  │  ├─ lod_n_loq.py
│  │  ├─ precision.py
│  │  ├─ accuracy.py
│  │  └─ add_params.py
│  │
│  ├─ ack_mva/                       # Acknowledgements
│  │  └─ credits.py
|  ├─ app/
│  │  ├─ __init__.py
│  │  └─ startup.py
│  │  
|  ├─ static/
│  │  ├─ icons/
│  │  │  ├─ logo.ico
│  │  │  ├─ logo.png
│  │  │  └─ logo_no_bg.png                
│  │  ├─ example.xlsx                # Blank template dataset
│  │  └─ Amph_example_dataset.xlsx   # Bundled amphetamine example
│  │
│  ├─ utilities/                     # Backend functions
│     ├─ os_utilities.py             # Handlers for folders
│     ├─ pd_utilities.py             # Pandas utilities
│     ├─ plotly_utilities.py         # Graphs
│     └─ stat_test.py                # Statistical tests
│  
└─

```

## Credits

This software was developed by a team of contributors, including:
* [Giovanni Solarino](https://dott-scm.campusnet.unito.it/do/studenti.pl/Show?_id=982868#profilo), PhD Student in Chemical and Materials Sciences, University of Turin, Department of Chemistry
* [Eugenio Alladio](https://dott-scm.campusnet.unito.it/do/docenti.pl/Show?_id=ealladio#tab-profilo), Assistant Professor, University of Turin, Department of Chemistry
* [Marco Vincenti](https://dott-scm.campusnet.unito.it/do/docenti.pl/Show?_id=mvincent#tab-profilo), Full Professor, University of Turin, Department of Chemistry


This software uses the following open source packages:

- [Numpy](https://numpy.org/)
- [SciPy](https://scipy.org/)
- [Statsmodels](https://www.statsmodels.org/stable/)
- [Matplotlib](https://matplotlib.org/)
- [Plotly](https://plotly.com/)
- [NiceGUI](https://nicegui.io/)

## Related

If you're looking to enhance your validation study with additional key parameters, we've got you covered! 

[Contact us!](https://www.databloom.it/)

## How To Cite Us

Upcoming publication


## License

FREEWARE
[TO ADD]

---
