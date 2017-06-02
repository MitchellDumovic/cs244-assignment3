from mininet.node import Controller
import os

POXDIR = os.getcwd() + '/../..'

class DCELLPOX( Controller ):
    def __init__( self, name, cdir=POXDIR,
                  command='python pox.py', cargs=('log --file=dcell.log,w openflow.of_01 --port=%s ext.dcell_controller' ),
                  **kwargs ):
        Controller.__init__( self, name, cdir=cdir,
                             command=command,
                             cargs=cargs, **kwargs )
controllers={ 'dcell': DCELLPOX }
