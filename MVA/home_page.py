from nicegui import ui

def about() -> None:

    with ui.column(align_items='center'):
        ui.markdown('''
                    ## **About**
                     _Explore how MVA works_                  
                    ''')
    ui.separator().props("color=black size=2px").style('width: 85vw')

    with ui.grid(columns=2):
        ui.markdown('''
                ### **_Change your approach to validation protocols!_**
                </br>
                Recent technological advancements have catalyzed the development of new analytical methods 
                for the identification and quantification of substances in complex matrices. 
                To ensure reliable results and method robustness, it is imperative to **validate the method** prior to its deployment in routine applications.
                \n\n
                Methods Validation App aims to provide a systematic workflow, organized across multiple pages, for the validation of analytical methods. 
                Moreover, MVA provides the ability to calculate numerous additional parameters 
                essential for _**ISO 17025**_ compliance, enhancing both efficiency and accuracy in the process.
                \n\n
                **_More information can be found in the documentation and/or in bibliography._**     
                
                ''').classes('padding: 40px')
        ui.image('.\icons\logo_no_bg.png').props('fit=scale-down')

        ui.add_css('''
            .q-timeline__title {
            display: none;
            }
            ''')

        with ui.column().classes('w-full max-w-screen-lg p-4'):
                with ui.timeline(side='right').classes('w-full'):
                        ui.timeline_entry('.xls/.xlsx, .txt o .csv format',
                      subtitle='Import data', icon='upload_file')
                        ui.timeline_entry('Instrumental behaviour response, weight and model order selection',
                      subtitle='Calibration', icon='r_analytics')
                        ui.timeline_entry('Hubaux and Vos method',
                      subtitle='Limit Of Detection', icon='r_science')
                        ui.timeline_entry('Intra and inter day',
                        subtitle='Precision and accuracy', icon='ads_click')
                        ui.timeline_entry('Sensitivity, selectivity, carry-over ,matrix effect, recovery',
                        subtitle='Additional parameters evaluation', icon='tune')
            
        with ui.card():
                ui.markdown('### Bibliography')
                with ui.card_section():
                    ui.markdown("[1] Alladio, E., Amante, E., Bozzolino, C., Seganti, F., Salomone, A., Vincenti, M., & Desharnais, B. (2020). Effective validation of chromatographic analytical methods: the illustrative case of androgenic steroids. Talanta, 215, 120867.") 
                    ui.link("doi.org/10.1016/j.talanta.2020.120867", "https://doi.org/10.1016/j.talanta.2020.120867", new_tab=True)
                    ui.markdown("[2] Alladio, E., Amante, E., Bozzolino, C., Seganti, F., Salomone, A., Vincenti, M., & Desharnais, B. (2020). Experimental and statistical protocol for the effective validation of chromatographic analytical methods. MethodsX, 7, 100919.") 
                    ui.link("doi.org/10.1016/j.mex.2020.100919", "https://doi.org/10.1016/j.mex.2020.100919", new_tab=True)
                    ui.markdown("[3] Desharnais, B., Camirand-Lemyre, F., Mireault, P., & Skinner, C. D. (2017). Procedure for the selection and validation of a calibration model I—description and application. Journal of Analytical Toxicology, 41(4), 261-268.") 
                    ui.link("doi.org/10.1093/jat/bkx001", "https://doi.org/10.1093/jat/bkx001", new_tab=True)
                    ui.markdown("[4] Desharnais, B., Camirand-Lemyre, F., Mireault, P., & Skinner, C. D. (2017). Procedure for the selection and validation of a calibration model II—theoretical basis. Journal of Analytical Toxicology, 41(4), 269-276.") 
                    ui.link("doi.org/10.1093/jat/bkx002", "https://doi.org/10.1093/jat/bkx002", new_tab=True)
                    ui.markdown("[5] Raposo, F. (2016). Evaluation of analytical calibration based on least-squares linear regression for instrumental techniques: A tutorial review. TrAC Trends in Analytical Chemistry, 77, 167-185.")
                    ui.link("doi.org/10.1016/j.trac.2015.12.006", "https://doi.org/10.1016/j.trac.2015.12.006", new_tab=True)
                    ui.markdown("[6] Andrade, J. M., & Gómez-Carracedo, M. P. (2013). Notes on the use of Mandel's test to check for nonlinearity in laboratory calibrations. Analytical Methods, 5(5), 1145-1149.") 
                    ui.link("doi.org/10.1039/C2AY26400E", "https://doi.org/10.1039/C2AY26400E", new_tab=True)
                    ui.markdown("[7] Hubaux, A., & Vos, G. (1970). Decision and detection limits for calibration curves. Analytical chemistry, 42(8), 849-855.")
                    ui.link("doi.org/10.1021/ac60290a013", "https://doi.org/10.1021/ac60290a013", new_tab=True)
                    ui.markdown("[8] Levene, H. (1960). Robust tests for equality of variances. Contributions to probability and statistics, 278-292.")
                
    ui.separator()