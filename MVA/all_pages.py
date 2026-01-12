from nicegui import ui
from ack_mva.credits import credits
from pages.import_data import content
from pages.linearity import linearity
from pages.lod_n_loq import lod_loq
from pages.precision import precision
from pages.accuracy import accuracy
from pages.add_params import add_params

def create() -> None:
    ui.page('/import_data/')(content)
    ui.page('/credits/')(credits)
    ui.page('/linearity/')(linearity)
    ui.page('/lod_n_loq/')(lod_loq)
    ui.page('/precision/')(precision)
    ui.page('/accuracy/')(accuracy)
    ui.page('/add_params/')(add_params)

if __name__ == '__main__':
    create()