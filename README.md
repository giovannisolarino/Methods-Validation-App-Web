
<h1 align="center">
  <br>
  <a><img src="./logo_no_bg.png"
  width="400"></a>
  <br>
  Methods Validation App
<br>
</h1>
<h4 align="center">Analytical method validation software written in Python.</h4>

<p align="center">
  <a href="#key-features">Key Features</a> •
  <a href="#web-app">Web-app</a> •
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
MVA (Version 1.0) is now freely available at [mva.databloom.eu](https://mva.databloom.eu/).

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
|  ├─ main.py                        # Main entry
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
│  │  ├─ example.xlsx                # Template dataset
│  │  └─ example.xlsx
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
