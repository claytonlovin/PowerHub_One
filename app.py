
#from tkinter import Entry
#from traceback import print_tb
from setting.config import *
from router.router import *
import os

'''if __name__ == '__main__':
    app.run(debug=True)
'''

if __name__ == '__main__':
    app.run(port=os.getenv("PORT", default=5000))
