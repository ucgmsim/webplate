# Using Plot.ly, HTMX, and Flask for Dynamic Dashboards with Minimal Javascript

We generate a lot of data that benefits from visualisation. This
document outlines a framework for interactive data visualisation that:

0.  Requires minimal (usually no) frontend code.
1.  Can be maintained in the language we all work with.
2.  Takes advantage of all the existing scientific code we have written
    in Python.
3.  Allows us to utilise the existing scientific library stack (pandas,
    numpy, scipy, etc) that is unavailable in JavaScript.
4.  Enables interactive websites (i.e. changes to the webpage without
    full page loads).
5.  Is performant, browser friendly, and conforms to the user's standard
    expectations of how a browser works.

To achieve these goals we are going to make use of
[*plotly*](https://plotly.com/python/) for HTML based data
visualisation, [*HTMX*](https://htmx.org/) to eliminate frontend code,
and the usual [*flask*](https://flask.palletsprojects.com/) and
[*jinja*](https://jinja.palletsprojects.com/) for backend templating.

# Setup: Building a Website with Flask

Flask is a simple Python package for hosting websites. To begin with
flask, you should follow the [*setup
guide*](https://flask.palletsprojects.com/en/stable/tutorial/factory/)
which details the most up-to-date canonical way to structure a flask
project. Some details on this guide may change for your project.

As of the time of writing the canonical flask structure for a
"hello_world" project looks like the following:

- hello_world

  - app

    - \_\_init\_\_.py

    - db.py (optional).

    - views.py

    - templates

      - base.html

      - views

        - index.html

    - static

      - plotly.min.js.gz
      - htmx.min.js.gz

  - pyproject.toml

The contents of *\_\_init\_\_.py*  will be the definition of your app,
and then *views.py*  contains the routes. You should break up the
*views.py*  module into a number of smaller modules if you have many
routes.  The *db.py*  file usually contains code for extracting data
from a dataset (SQLite db, parquet file, etc) – you may not need this if
your dataset is simple. The *templates*  directory contains all the html
templates, including a *base.html*  which contains common HTML setup,
and a *views*  subdirectory containing the HTML for the routes defined
in *views.py* . Finally, the *static* directory contains our frontend
libraries plotly and htmx, alongside any CSS styles or scripts you
choose to include. [*You can find this template repo on
GitHub*](https://github.com/ucgmsim/webplate).

## Python

**\_\_init\_\_.py**

from flask import Flask

from pathlib import Path

def create_app(test_config=None):

\# create and configure the app

app = Flask(\_\_name\_\_, instance_relative_config=True)

app_path = Path(app.instance_path)

app.config.from_mapping(

DATABASE=app_path / 'dataset.parquet', \# or an SQLite db, or SHP file,
etc.

)

if test_config is None:

\# load the instance config, if it exists, when not testing

app.config.from_pyfile('config.py', silent=True)

else:

\# load the test config if passed in

app.config.from_mapping(test_config)

\# import our views and register them with the app.

from hello_world import views

   app.register_blueprint(views.bp)

\# ensure the instance folder exists

app_path.mkdir(exist_ok=True)

return app

**views.py**

import flask

bp = Blueprint('views', \_\_name\_\_)

@bp.route('/', methods=\['GET'\])

def index():

return flask.render_template('views/index.html')

## HTML

**base.html**

\<!DOCTYPE html\>

\<html lang="en"\>

\<head\>

\<meta charset="UTF-8"\>

\<meta name="viewport" content="width=device-width, initial-scale=1.0"\>

\<meta http-equiv="X-UA-Compatible" content="IE=edge"\>

\<title\>{% block title %}Flask App{% endblock %}\</title\>

\<link rel="stylesheet" href="{{ url_for('static',
filename='styles.css') }}"\>

\<!-- Load HTMX --\>

\<script src="{{ url_for('static', filename='htmx.min.js.gz')
}}"\>\</script\>

\<!-- Load Plotly --\>

\<script src="{{ url_for('static', filename='plotly.min.js.gz')
}}"\>\</script\>

{% block scripts %}

\<!-- Add additional scripts here --\>

{% endblock %}

{% block head %}{% endblock %}

\</head\>

\<body\>

\<header\>

\<nav\>

\<!-- Add navigation items here --\>

\</nav\>

\</header\>

\<main\>

{% block content %}

{% endblock %}

\</main\>

\</body\>

\</html\>

**index.html**

{% extends "base.html" %}

{% block title %}

Hello World

{% endblock %}

{% block content %}

\<section\>

\<h1\>Hello, World!\</h1\>

\<p\>Welcome to your Flask app using HTMX and Plotly!\</p\>

\</section\>

{% endblock %}

# Using Plot.ly and Flask together

Let's take the template we began with and build a website that can view
intensity measure data from simulations on a map. We'll simply assume
that you just want to view one set of intensity measures from a
particular simulation. An easy extension of this would be allowing the
user to upload a parquet file for analysis first.

To begin, download the [*stations and intensity
measures*](https://www.dropbox.com/scl/fo/fwouzfp9qfo2c8vzdlvag/AC8PiNtkPsXNr4FQE86DpLc?rlkey=m45bsbonrr0mk8xwzkvloxsdj&st=j6502kjq&dl=0)
and save them in the instance folder of your app

- hello_world

  - app

    - \_\_init\_\_.py

    - views.py

    - templates

      - base.html

      - views

        - index.html

    - static

      - plotly.min.js.gz
      - htmx.min.js.gz

  - pyproject.toml

  - instance

    - intensity_measures.parquet
    - stations.ll

Then copy the following into the views.py and index.html:

**views.py**

import flask

import pandas as pd

from pathlib import Path

import plotly.express as px

\# Create a Flask Blueprint for the views

bp = flask.Blueprint("views", \_\_name\_\_)

@bp.route("/", methods=\["GET"\])

def index() -\> str:

"""Serve the standard index page."""

\# Access the instance folder for application-specific data

instance_path = Path(flask.current_app.instance_path)

\# Load intensity measures data from a Parquet file

df = (

pd.read_parquet(instance_path / "intensity_measures.parquet")

.reset_index() \# Ensure a clean index for later operations

.set_index(\["station"\]) \# Set 'station' as the index for easier
merging

)

\# Extract unique intensity measures for UI dropdown or selection

intensity_measures = df\["intensity_measure"\].unique()

\# Retrieve selected intensity measure or default to "PGA"

im = 'PGA'

\# Filter the dataframe for the selected intensity measure

df = df\[df\["intensity_measure"\] == im\]

\# Load station location data from a text file

locations = pd.read_csv(

instance_path / "stations.ll",

sep=r"\s+", \# Handle whitespace-delimited file

header=None, \# File does not have a header row

names=\["longitude", "latitude", "station"\], \# Assign column names

).set_index("station") \# Set 'station' as index for merging

\# Join location data with intensity measure data

df = df.join(locations)

\# Calculate the center of the map for visualization

centre_lat = df\["latitude"\].mean()

centre_lon = df\["longitude"\].mean()

\# Add a constant size column for consistent marker sizes in the map

df\["size"\] = 0.5

\# Create an interactive scatter map using Plotly

im_map = px.scatter_map(

df,

lat="latitude", \# Column specifying latitude

lon="longitude", \# Column specifying longitude

color="rotd50", \# Column specifying marker color

hover_name=df.index, \# What to display when hovering over a marker

hover_data={

"rotd50": ":.2e", \# Format numerical values in scientific notation

"rotd100": ":.2e",

"000": ":.2e",

"090": ":.2e",

"ver": ":.2e",

},

size="size", \# Marker size

center={"lat": centre_lat, "lon": centre_lon}, \# Map center

)

\# Render the map and data in an HTML template

return flask.render_template(

"views/index.html",

map=im_map.to_html(

full_html=False, \# Embed only the necessary map HTML

include_plotlyjs=False, \# Exclude Plotly.js library (assume it's loaded
separately)

default_height="85vh", \# Set the map height

),

)

**index.html**

{% extends "base.html" %}

{% block title %}

Hello World

{% endblock %}

{% block content %}

\<section\>

\<h1\>Map of Intensity Measures\</h1\>

\</section\>

\<section role="figure" style="height: 100vh;"\>

{{map \| safe}}

\</section\>

{% endblock %}

When you run the app with *flask --app app run*  in the root of the
project you should see this webpage at *localhost:5000* 

<img src="media/image1.tmp" style="width:4.875in;height:4.54167in" />

(Obviously, no points for style here, it's just a demo)

Let's review the parts of this code that may be unfamiliar to you:

im_map = px.scatter_map(

df,

lat="latitude",

lon="longitude",

color="rotd50",

hover_name=df.index,

hover_data={

"rotd50": ":.2e",

"rotd100": ":.2e",

"000": ":.2e",

"090": ":.2e",

"ver": ":.2e",

},

size="size",

center={"lat": centre_lat, "lon": centre_lon},

)

return flask.render_template(

"views/index.html",

map=im_map.to_html(

full_html=False, include_plotlyjs=False, default_height="85vh"

),

)

This creates a plotly map instance and then passes it to the template to
render. There are [*lots of visualisation options with plotly
express*](https://plotly.com/python/plotly-express/) and then [*even
more with plotly graph
objects*](https://plotly.com/python/graph-objects/). The most
interesting are the map ones:

- Scatter maps, which is what we are using
- Line maps, which are the same with lines,
- Choropleth maps, which are like what Folium uses.

The *full_html*  and *include_plotlyjs*  options are important, they
ensure that plotly spits out only the map and no headers or bundled
plotly version.

\<section role="figure"\>

{{map \| safe}}

\</section\>

This is the actual injection of the map into html. You need to mark the
map as safe HTML using the safe filter. If you do not do this Flask will
escape the HTML markup automatically (see below).

<img src="media/image2.tmp" style="width:4.875in;height:4.54167in" />

## Adding Search Queries

We'd like to make this super interactive. Ideally any filter you could
apply in Pandas you should be able to apply to our intensity measures.
Turns out, this is really easy! The query is the pandas dataframe query
method.

Make the following changes to the views and html:

**views.py**

import flask

import pandas as pd

from pathlib import Path

import plotly.express as px

\# Create a Flask Blueprint for the views

bp = flask.Blueprint("views", \_\_name\_\_)

@bp.route("/", methods=\["GET"\])

def index() -\> str:

"""Serve the standard index page."""

\# Access the instance folder for application-specific data

instance_path = Path(flask.current_app.instance_path)

\# Load intensity measures data from a Parquet file

df = (

pd.read_parquet(instance_path / "intensity_measures.parquet")

.reset_index() \# Ensure a clean index for later operations

.set_index(\["station"\]) \# Set 'station' as the index for easier
merging

)

\# Extract unique intensity measures for UI dropdown or selection

intensity_measures = df\["intensity_measure"\].unique()

\# Retrieve selected intensity measure or default to "PGA"

im = flask.request.args.get(

"intensity_measure",

default="PGA", \# Default value if no query parameter is provided

)

\# Retrieve an optional custom query from request arguments

query = flask.request.args.get("query", default=None)

\# Filter the dataframe for the selected intensity measure

df = df\[df\["intensity_measure"\] == im\]

\# Load station location data from a text file

locations = pd.read_csv(

instance_path / "stations.ll",

sep=r"\s+", \# Handle whitespace-delimited file

header=None, \# File does not have a header row

names=\["longitude", "latitude", "station"\], \# Assign column names

).set_index("station") \# Set 'station' as index for merging

\# Join location data with intensity measure data

df = df.join(locations)

\# Apply custom query filtering if provided

if query:

df = df.query(query)

\# Calculate the center of the map for visualization

centre_lat = df\["latitude"\].mean()

centre_lon = df\["longitude"\].mean()

\# Add a constant size column for consistent marker sizes in the map

df\["size"\] = 0.5

\# Create an interactive scatter map using Plotly

im_map = px.scatter_map(

df,

lat="latitude", \# Column specifying latitude

lon="longitude", \# Column specifying longitude

color="rotd50", \# Column specifying marker color

hover_name=df.index, \# What to display when hovering over a marker

hover_data={

"rotd50": ":.2e", \# Format numerical values in scientific notation

"rotd100": ":.2e",

"000": ":.2e",

"090": ":.2e",

"ver": ":.2e",

},

size="size", \# Marker size

center={"lat": centre_lat, "lon": centre_lon}, \# Map center

)

\# Render the map and data in an HTML template

return flask.render_template(

"views/index.html",

map=im_map.to_html(

full_html=False, \# Embed only the necessary map HTML

include_plotlyjs=False, \# Exclude Plotly.js library (assume it's loaded
separately)

default_height="85vh", \# Set the map height

),

selected_im=im, \# Pass the selected intensity measure for the template

query=query, \# Pass the query back for persistence in UI

intensity_measures=intensity_measures, \# Pass all intensity measures
for UI dropdown

)

**index.html**

{% extends "base.html" %}

{% block title %}

Hello World

{% endblock %}

{% block content %}

\<section\>

\<h1\>Map of Intensity Measures\</h1\>

\</section\>

\<!-- Form to allow user input for filtering data --\>

\<form method="GET" action="{{url_for('views.index')}}"\>

\<!-- Text input for a custom query, passed as the 'query' parameter in
the URL --\>

\<input

name="query"

placeholder="Input your pandas-compatible search query"

value="{{query or ''}}" \<!-- Prepopulate with the current query if it
exists --\>

\>\</input\>

\<!-- Dropdown to select an intensity measure --\>

\<label for="intensity_measure"\>Select an intensity measure\</label\>

\<select name="intensity_measure"\>

\<!-- Populate dropdown options dynamically from the list of intensity
measures --\>

{% for im in intensity_measures %}

\<option

value="{{im}}"

{% if selected_im == im %}selected{% endif %} \<!-- Mark the current
selection --\>

\>

{{im}}

\</option\>

{% endfor %}

\</select\>

\<!-- Submit button to trigger a search --\>

\<button\>Search\</button\>

\</form\>

\<!-- Section to render the Plotly map --\>

\<section role="figure"\>

{{map \| safe}} \<!-- Render the Plotly map as raw HTML. 'safe' prevents
auto-escaping of HTML content --\>

\</section\>

{% endblock %}

The real magic is the following lines of code:

\# Apply custom query filtering if provided

if query:

df = df.query(query)

This makes use of the *pd.DataFrame.query*  method and it's powerful
syntax. It implements a psuedo-Python like language to query dataframes
with a search string. Here is an example of this in action filtering for
all stations where the rotd100 PGA to rotd50 PGA ratio exceeds 1.3,
indicating higher than average directionality. You should read [*the
docs for this
method*](https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.query.html).

<img src="media/image3.tmp" style="width:4.875in;height:4.54167in" />

Notice also that because this is all plain HTML and a boring compliant
server side rendered web app we get one extra feature for free: linkable
data analytics. If you open
[*http://127.0.0.1:5000/?query=rotd100+%2F+rotd50+%3E+1.3&intensity_measure=PGA*](http://127.0.0.1:5000/?query=rotd100+%2F+rotd50+%3E+1.3&intensity_measure=PGA)
you can see exactly the same  view that produced this picture. If you
want a similar view with CAV, then you can [*click this link and view
that
too*](http://127.0.0.1:5000/?query=rotd100+%2F+rotd50+%3E+1.15&intensity_measure=CAV).

# Adding Interactivity with HTMX

Beside some polish, the website is useful as-is. However, from a UX
standpoint, the most glaring issue is that you receive no feedback if
the pandas expression you pass is bad until you submit and get hit with
a nasty server error 500. Wouldn't it be nice if it gave you a popup
underneath that told in real-time whether the request was valid?

For this, we can (and I would encourage you to) use the [*flask request
flash
functionality*](https://flask.palletsprojects.com/en/stable/patterns/flashing/).
However to demo a more interactive approach, one that generalises to far
more than just input validation, we will use HTMX instead. HTMX is a
javascript library designed to minimise the amount of javascript you
write. It's built on the principle of a Hypermedia system: events
trigger requests to the server and the server-side logic returns HTML.
Note this is very different to the traditional web dev model where a
framework requests and receives JSON from an API and then renders it on
the client into HTML.

<img src="media/image4.tmp" style="width:4.875in;height:2.89583in" />

To make our error validation in a traditional frontend-backend split, we
would usually either attempt to parse the query on the client side, but
more likely we'd send the query to an API endpoint that validates the
query and then use the response somehow for feedback. With HTMX, we
instead:

11. Create an error box template.
12. Make a new endpoint that returns just the HTML for the error.
13. Instruct HTMX to query that endpoint on each keypress.

Let's do that now. We now create a new file *app/templates/error.html* 

**error.html**

\<p style="color: red;"\>{{error}}\</p\>

And then a new validate endpoint that either returns an empty string if
the query is valid, or the error HTML if not.

@bp.route("/validate", methods=\["GET"\])

def validate():

query = flask.request.args.get("query", None)

if not query:

return ""

\# Create a dummy dataframe to ensure the column names are present

dummy_df = pd.DataFrame(

columns=\[

"station",

"latitude",

"longitude",

"000",

"090",

"ver",

"geom",

"rotd50",

"rotd100",

\]

)

try:

dummy_df.query(query)

except (

ValueError,

SyntaxError,

UnboundLocalError,

pd.errors.UndefinedVariableError,

) as e:

return flask.render_template("error.html", error=e)

return ""

Finally, we update index.html to trigger a call to this endpoint when
the user has stopped typing and the text has changed.

**index.html**

\<--! The rest of index.html is omitted as it is unchanged --\>

\<input name='query' hx-get="/validate" hx-trigger="keyup delay:300ms
changed" hx-target="#error" placeholder='Input your pandas-compatible
search query' value="{{query or ''}}"\>\</input\>

If you do this and put in an erroneous string in the search query, you
now get some nice feedback

<img src="media/image5.tmp" style="width:4.875in;height:0.67708in" />

Notice what we didn't have to write a single line of javascript to get
this functionality to work. What's more, because we aren't doing the
validation client-side and use the bona fide *pd.DataFrame.query*  our
query validation is 100% correct: it validates it will search correctly.
You could imagine other kinds of checks you'd want to do with this
endpoint, mainly checking that the right columns for plotting are
present etc.

You can be proficient with HTMX in an afternoon. If you're interested in
what else can be done with HTMX, [*read the one-page
docs*](https://htmx.org/docs/).

# Extra Ideas for Data Analytics

There are lots of things you can do with this kind of work, for example:

- Allow users to download the results of their searches,
- Reexport your plots as a high-quality SVG/PNG so researchers can
  easily include it in their presentations (plotly supports this),
- [Custom plot controls](https://plotly.com/python/custom-buttons/) to
  change the view of the same graph (e.g. a 3d visualisation vs a
  contour plot).
- LLM backend query inputs.

That last one is interesting and warrants  elaboration. ChatGPT is very
adept at producing DataFrame compatible query strings from natural
language input. If you additionally provide statistics and context about
the columns in the dataframe you can get powerful introspection features
for free. For example:

- You could provide a histogram of each dataframe column prior to the
  user query, and then ChatGPT can generate queries like "Get the top
  10% of all PGA IMs".
- You could provide definitions of all the IMs and ask it to "Find the
  most direction dependent sites".
- You can search based on qualitative values rather than physical ones:
  "Estimate which sites would have a high MMI (qualitative measure of
  ground motion) value from their PGV."

Especially for public facing dashboards this kind of ability is really
powerful.

# Some Style Points

HTML5 has come a long way from the bad old days of yore, and browsers
are quite opinionated about how you should write websites. In
particular, there are a large number of semantic HTML tags that you can
use that provide information to the browser and the user to enhance the
experience. Tags you should be familiar with include:

- header
- main
- nav
- section
- footer

Avoid needless *div* spam. A browser doesn't know what a *div*  is and
can't interpret the semantics of it. Additionally, and especially if the
dashboard is public facing, you should make use of the *aria-role*  HTML
attributes to enhance accessibility for those with screen readers (along
with other considerations like *alt* on images and figures). The most
important *aria-role* for our purposes is the *figure*  role which
instructs the browser that the section or div contains a figure. Another
advantage of the above semantic tags is that you do not need to provide
*aria-role* for them since the tag conveys that information to the
browser already. In short: accessible websites and well-written websites
are usually isomorphic, if you find yourself struggling to accommodate
this then you probably wrote your website wrong.

HTMX, and JavaScript more broadly, are really powerful tools. However,
just because you have a powerful tool doesn't mean that you should use
it. We could've easily made the query field in this example website
interactive with HTMX, sending a map back when you click the send button
rather than loading a new page. However, this would've required more
code to maintain, and we loose a bunch of features the browser gives us
for free: form data saving, linking to search results, etc. Browser
maintainers are pretty smart and spend a lot of time making boring old
HTML behave in a way users expect, so there is no point in reinventing
the wheel because you dislike the flashing screen that occurs when you
hit enter in the form. To summarise:

- Use HTML5 semantic tags.
- Use HTMX/JavaScript where it's needed (but no more).
- [The Zen of Python](https://peps.python.org/pep-0020/) applies just as
  much to websites as Python code.

For CSS styling, provided you use semantic HTML tags, classless CSS
frameworks like [*Almond
CSS*](https://alvaromontoro.github.io/almond.css/demo/old/) provide a
great template for writing a webpage that doesn't make your eyes bleed
without writing a lot of CSS yourself.
