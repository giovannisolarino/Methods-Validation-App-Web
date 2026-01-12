import theme
from nicegui import ui


def credits() -> None:
    with theme.frame('Credits'):

        # --- Title -----------------------------------------------------------
        ui.markdown('## **Credits**')
        ui.separator().props('color=black size=2px').style('width: 90vw; margin:auto;')

        # --- Intro text ------------------------------------------------------
        # If you want pure HTML, ui.html is safer than ui.markdown here
        ui.html('''
            <div style="text-align:center; font-size:1.1rem; margin-top:20px;">
                <b>MVA</b> has been developed through a collaborative effort between
                <b>DataBloom</b> and the <b>University of Turin</b>, combining academic expertise with
                software innovation.
            </div>
        ''')

        ui.separator().props('color=black size=1px').style('width: 60vw; margin:20px auto;')

        # --- Contributors title ---------------------------------------------
        ui.html('''
            <div style="text-align:center; font-size:1.4rem; margin-top:20px; font-weight:bold;">
                Contributors
            </div>
        ''')

        # --- Cards row -------------------------------------------------------
        with ui.row().classes('w-full gap-6 q-pa-md'):

            # Giovanni
            with ui.card().classes('shadow-md').style(
                    'border: 1px solid #9ec239; width:330px; border-radius:10px; padding:15px;'):
                ui.markdown('**Giovanni Solarino**').classes('text-lg')
                ui.markdown('PhD Student in Chemical and Materials Science')
                ui.markdown('University of Turin')
                ui.link(
                    'giovanni.solarino@unito.it',
                    'mailto:giovanni.solarino@unito.it',
                    new_tab=True,
                )

            # Alladio
            with ui.card().classes('shadow-md').style(
                    'border: 1px solid #9ec239; width:330px; border-radius:10px; padding:15px;'):
                ui.markdown('**Eugenio Alladio**').classes('text-lg')
                ui.markdown('Associate Professor')
                ui.markdown('University of Turin')
                ui.link(
                    'eugenio.alladio@unito.it',
                    'mailto:eugenio.alladio@unito.it',
                    new_tab=True,
                )

            # Vincenti
            with ui.card().classes('shadow-md').style(
                    'border: 1px solid #9ec239; width:330px; border-radius:10px; padding:15px;'):
                ui.markdown('**Marco Vincenti**').classes('text-lg')
                ui.markdown('Full Professor')
                ui.markdown('University of Turin')
                ui.link(
                    'marco.vincenti@unito.it',
                    'mailto:marco.vincenti@unito.it',
                    new_tab=True,
                )

            # DataBloom
            with ui.card().classes('shadow-md').style(
                    'border: 1px solid #9ec239; width:330px; border-radius:10px; padding:15px;'):
                ui.markdown('**DataBloom s.r.l.**').classes('text-lg')
                ui.markdown('Data Science and Chemometrics solutions')
                ui.link(
                    'info@databloom.it',
                    'mailto:info@databloom.it',
                    new_tab=True,
                )

        # --- Licensing section ----------------------------------------------
        ui.html('''
            <div style="
                text-align:left;
                font-size:1.45rem;
                font-weight:600;">
                Licensing & Availability
            </div>
        ''')

        ui.html('''
            <div style="
                max-width:80vw;
                margin:18px auto 0 auto;
                text-align:left;
                font-size:1.05rem;
                line-height:1.55;">
                <b>MVA</b> is distributed as <b>freeware</b> for academic and research use.
                A full professional version with enhanced capabilities is available upon request.<br>
                For commercial licensing, enterprise deployments, or tailored integrations,
                please contact <b>DataBloom</b>.
            </div>
        ''')

        # --- Bug Report Panel -----------------------------------------------
        ui.separator().props('color=black size=1px').style(
            'width: 60vw; max-width:800px; margin: 20px auto;')

        with ui.card().classes('shadow-lg').style('''
            width:520px;
            margin: 0 auto 30px auto;
            border-radius:14px;
            border:1px solid #9ec239;
            padding:22px;
            background:#ffffff;
        '''):
            ui.html('''
                <div style="
                    text-align:center;
                    font-size:1.25rem;
                    font-weight:600;
                    margin-bottom:4px;">
                    Report an Issue
                </div>
            ''')

            ui.html('''
                <div style="
                    text-align:center;
                    font-size:1rem;
                    line-height:1.45;
                    margin-bottom:15px;
                    color:#444;">
                    If you encounter unexpected behavior, errors, or would like to propose
                    new features, please notify the development team.
                </div>
            ''')

            ui.button(
                'Report a Bug',
                icon='bug_report',
                color='negative',
                on_click=lambda: ui.run_javascript(
                    "window.open('https://forms.gle/MaC7pwzvCTfHSNkp6', '_blank');"
                ),
            ).props('rounded no-caps').classes('w-full')

        # --- Footer / Copyright ---------------------------------------------

        with ui.row().classes('w-full justify-center'):
            ui.html('''
        <div style="
            text-align:center;
            font-size:0.9rem;
            color:#555;">
            © 2025 MVA — DataBloom & University of Turin<br>
            <span style="font-size:0.80rem; color:#666;">
                Distributed as freeware for academic and research purposes.<br>
                For access to the complete version, please contact <b>DataBloom</b>.
            </span>
        </div>
    ''')

