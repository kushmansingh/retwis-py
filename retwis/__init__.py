from flask import Flask

app = Flask(__name__)
app.config.from_object('retwis.settings')

import retwis.views