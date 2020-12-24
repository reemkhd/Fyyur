#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for, abort, jsonify
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from flask_migrate import Migrate
from sqlalchemy import DateTime, func
import re
import datetime
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)
migrate = Migrate(app, db)

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#

class Genres(db.Model):
    __tablename__ = 'Genres'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120))

genres_venue = db.Table('genres_venue',
    db.Column('genres_id', db.Integer, db.ForeignKey('Genres.id'), primary_key=True),
    db.Column('venue_id', db.Integer, db.ForeignKey('Venue.id'), primary_key=True)
)

genres_artist = db.Table('genres_artist',
    db.Column('genres_id', db.Integer, db.ForeignKey('Genres.id'), primary_key=True),
    db.Column('artist_id', db.Integer, db.ForeignKey('Artist.id'), primary_key=True)
)

class Venue(db.Model):
    __tablename__ = 'Venue'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    address = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    website = db.Column(db.String(120))
    seeking_talent = db.Column(db.String(120))
    seeking_description = db.Column(db.String(120))

    genres = db.relationship('Genres', secondary=genres_venue, lazy='subquery',
        backref=db.backref('venue', lazy=True))
    shows = db.relationship('Show', backref='venue')
    def __repr__(self):
      return f'<Venue {self.id}, {self.name}>'

class Artist(db.Model):
    __tablename__ = 'Artist'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    website = db.Column(db.String(120))
    seeking_talent = db.Column(db.String(120))
    seeking_description = db.Column(db.String(120))

    genres = db.relationship('Genres', secondary=genres_artist, lazy='subquery',
            backref=db.backref('artist', lazy=True))
    shows = db.relationship('Show', backref='artist')
    def __repr__(self):
      return f'<Artist {self.id}, {self.name}>'


class Show(db.Model):
    __tablename__ = 'Show'

    id = db.Column(db.Integer, primary_key=True)
    start_time = db.Column(DateTime, nullable=False)
    venue_id = db.Column(db.Integer, db.ForeignKey('Venue.id'))
    artist_id = db.Column(db.Integer, db.ForeignKey('Artist.id'))
    def __repr__(self):
        return f'<Show {self.id} {self.start_time} artist_id={artist_id} venue_id={venue_id}>'

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#
'''
def format_datetime(value, format='medium'):
    date = dateutil.parser.parse(value)
    if format == 'full':
        format = "EEEE MMMM, d, y 'at' h:mma"
    elif format == 'medium':
        format = "EE MM, dd, y h:mma"
    return babel.dates.format_datetime(value, format)
    '''

#The code above is not working with me , this insted:
def format_datetime(date, format='%x %X'):
    # check whether the value is a datetime object
    if not isinstance(date, (datetime.date, datetime.datetime)):
        try:
            date = datetime.datetime.strptime(str(date), '%Y-%m-%d').date()
        except Exception:
            return date
    return date.strftime(format)

app.jinja_env.filters['datetime'] = format_datetime
#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
  all_city_state = Venue.query.with_entities(Venue.city, Venue.state).distinct()
  data=[]
  for city_state in all_city_state:
    venue_data =[]
    for venue in Venue.query.filter_by(state=city_state.state).filter_by(city=city_state.city).all():
      venue_data.append({
        'id':venue.id,
        'name':venue.name,
        'num_upcoming_shows': len(Show.query.join(Venue).filter(Show.venue_id==venue.id).filter(Show.start_time>datetime.datetime.now()).all())
      })
    data.append({
      'city':city_state.city,
      'state':city_state.state,
      'venues':venue_data
    })
  return render_template('pages/venues.html', areas=data)

@app.route('/venues/search', methods=['POST'])
def search_venues():
  search_term = request.form.get('search_term', '')
  all_venues = Venue.query.filter(Venue.name.ilike("%" + search_term + "%")).all()

  data = []
  count=0
  for venue in all_venues:
    count+=1
    data.append({
       "id": venue.id,
       "name": venue.name,
       "num_upcoming_shows": len(Show.query.join(Venue).filter(Show.venue_id==venue.id).filter(Show.start_time>datetime.datetime.now()).all())
    })

  response={
    "count": count,
    "data": data
  }
  return render_template('pages/search_venues.html', results=response, search_term=search_term)

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  venue_data = Venue.query.get(venue_id)

  if not venue_data:
    abort(500)
  else:
    for genre in venue_data.genres:
      gen = [genre.name]

    past_shows = []
    for show in Show.query.join(Artist).filter(Show.venue_id==venue_id).filter(Show.start_time<datetime.datetime.now()).all():
      past_shows.append({
        "artist_id": show.artist_id,
        "artist_name": show.artist.name,
        "artist_image_link": show.artist.image_link,
        "start_time": show.start_time
      })

    upcoming_shows = []
    for show in Show.query.join(Artist).filter(Show.venue_id==venue_id).filter(Show.start_time>datetime.datetime.now()).all():
      upcoming_shows.append({
        "artist_id": show.artist_id,
        "artist_name": show.artist.name,
        "artist_image_link": show.artist.image_link,
        "start_time": show.start_time
      })

    data = {
            "id": venue_id,
            "name": venue_data.name,
            "genres": gen,
            "address": venue_data.address,
            "city": venue_data.city,
            "state": venue_data.state,
            "phone": venue_data.phone,
            "website": venue_data.website,
            "facebook_link": venue_data.facebook_link,
            "seeking_talent": venue_data.seeking_talent,
            "seeking_description": venue_data.seeking_description,
            "image_link": venue_data.image_link,
            "past_shows": past_shows,
            "past_shows_count": len(past_shows),        
            "upcoming_shows": upcoming_shows,
            "upcoming_shows_count": len(upcoming_shows)
    }

  return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  form = VenueForm()
  name = form.name.data
  city = form.city.data
  stat = form.state.data
  add = form.address.data
  phone = form.phone.data
  phone = re.sub('\D', '', phone)
  genres = form.genres.data
  image_link = form.image_link.data
  facebook_link = form.facebook_link.data
  seeking_talent = True if form.seeking_talent.data == 'Yes' else False
  seeking_description = form.seeking_description.data
  website = form.website.data

  error=False

  try:
    venue = Venue(
      name=name, 
      city=city, 
      state=stat, 
      address=add, 
      phone=phone, 
      image_link=image_link, 
      facebook_link=facebook_link, 
      seeking_talent=seeking_talent, 
      seeking_description=seeking_description, 
      website=website)
    new_genres = Genres(name=genres)
    venue.genres.append(new_genres)
    db.session.add(venue)
    db.session.commit()
  except():
    error = True
    db.session.rollback()
  finally:
        db.session.close()
  if error:
    flash('An error occurred. Venue ' + name + ' could not be listed.')
  if not error:
    flash('Venue ' + request.form['name'] + ' was successfully listed!')
  return render_template('pages/home.html')

@app.route('/venues/<venue_id>/delete', methods=['DELETE'])
def delete_venue(venue_id):
  venue = Venue.query.get(venue_id)
  error = False
  venue_name = venue.name
  try:
    db.session.delete(venue)
    db.session.commit()
  except:
    error = True
    db.session.rollback()
  finally:
    db.session.close()
  if error:
    flash('An error occurred deleting venue' + venue_name)
  else:
    flash('Successfully removed venue ' + venue_name)
  return redirect(url_for('venues'))


#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  artists = Artist.query.all()
  data=[]
  for artist in artists:
    data.append({
      'id':artist.id,
      'name':artist.name
    })
  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  search_term = request.form.get('search_term', '')
  all_artists = Artist.query.filter(Artist.name.ilike("%" + search_term + "%")).all()

  data = []
  count=0
  for artist in all_artists:
    count+=1
    data.append({
       "id": artist.id,
       "name": artist.name,
       "num_upcoming_shows": len(Show.query.join(Artist).filter(Show.artist_id==artist.id).filter(Show.start_time>datetime.datetime.now()).all())
    })

  response={
    "count": count,
    "data": data
  }
  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  artist_data = Artist.query.get(artist_id)

  if not artist_data:
    abort(500)
  else:
    for genre in artist_data.genres:
      gen = [genre.name]

    past_shows = []
    for show in Show.query.join(Venue).filter(Show.artist_id==artist_id).filter(Show.start_time<datetime.datetime.now()).all():
      past_shows.append({
        "venue_id": show.venue_id,
        "venue_name": show.venue.name,
        "venue_image_link": show.venue.image_link,
        "start_time": show.start_time
      })

    upcoming_shows = []
    for show in Show.query.join(Venue).filter(Show.artist_id==artist_id).filter(Show.start_time>datetime.datetime.now()).all():
      upcoming_shows.append({
        "venue_id": show.venue_id,
        "venue_name": show.venue.name,
        "venue_image_link": show.venue.image_link,
        "start_time": show.start_time
      })

    data = {
            "id": artist_id,
            "name": artist_data.name,
            "genres": gen,
            "city": artist_data.city,
            "state": artist_data.state,
            "phone": artist_data.phone,
            "website": artist_data.website,
            "facebook_link": artist_data.facebook_link,
            "seeking_talent": artist_data.seeking_talent,
            "seeking_description": artist_data.seeking_description,
            "image_link": artist_data.image_link,
            "past_shows": past_shows,
            "past_shows_count": len(past_shows),        
            "upcoming_shows": upcoming_shows,
            "upcoming_shows_count": len(upcoming_shows)
    }

  return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  data = Artist.query.get(artist_id)
  form = ArtistForm(obj=data)

  for genre in data.genres:
      gen = [genre.name]

  artist={
    "id": artist_id,
    "name": data.name,
    "genres": gen,
    "city": data.city,
    "state": data.state,
    "phone": data.phone,
    "website": data.website,
    "facebook_link": data.facebook_link,
    "seeking_talent": data.seeking_talent,
    "seeking_description": data.seeking_description,
    "image_link": data.image_link
  }
  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  form = ArtistForm()
  artist = Artist.query.get(artist_id)
  error = False
  try:
    artist.name=form.name.data
    genres=form.genres.data
    artist.city=form.city.data
    artist.state=form.state.data
    artist.phone=form.phone.data
    artist.image_link=form.image_link.data
    artist.facebook_link=form.facebook_link.data
    artist.seeking_talent=form.seeking_talent.data
    artist.seeking_description=form.seeking_description.data
    artist.website=form.website.data
    edit_genres = Genres(name=genres)
    artist.genres.append(edit_genres)

    db.session.commit()
  except():
    error = True
    db.session.rollback()
  finally:
        db.session.close()
  if error: 
    flash('An error occurred. Artist could not be updated.')
  if not error: 
    flash('Artist was successfully updated!')
  return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  data = Venue.query.get(venue_id)
  form = VenueForm(obj=data)
  for genre in data.genres:
      gen = [genre.name]
  venue={
    "id": venue_id,
    "name": data.name,
    "genres": gen,
    "address": data.address,
    "city": data.city,
    "state": data.state,
    "phone": data.phone,
    "website": data.website,
    "facebook_link": data.facebook_link,
    "seeking_talent": data.seeking_talent,
    "seeking_description": data.seeking_description,
    "image_link": data.image_link
  }
  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  form = VenueForm()
  venue = Venue.query.get(venue_id)
  error = False
  try:
    venue.name=form.name.data
    genres=form.genres.data
    venue.city=form.city.data
    venue.state=form.state.data
    venue.address=form.address.data
    venue.phone=form.phone.data
    venue.image_link=form.image_link.data
    venue.facebook_link=form.facebook_link.data
    venue.seeking_talent=form.seeking_talent.data
    venue.seeking_description=form.seeking_description.data
    venue.website=form.website.data
    edit_genres = Genres(name=genres)
    venue.genres.append(edit_genres)

    db.session.commit()
  except():
    error = True
    db.session.rollback()
  finally:
        db.session.close()
  if error: 
    flash('An error occurred. Venue could not be updated.')
  if not error: 
    flash('Venue was successfully updated!')
  return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  form = ArtistForm()

  name = form.name.data
  city = form.city.data
  stat = form.state.data
  phone = form.phone.data
  phone = re.sub('\D', '', phone)
  genres = form.genres.data
  image_link = form.image_link.data
  facebook_link = form.facebook_link.data
  seeking_talent = True if form.seeking_talent.data == 'Yes' else False
  seeking_description = form.seeking_description.data
  website = form.website.data

  error=False

  try:
    artist = Artist(
      name=name, 
      city=city, 
      state=stat, 
      phone=phone, 
      image_link=image_link, 
      facebook_link=facebook_link, 
      website=website,
      seeking_talent=seeking_talent, 
      seeking_description=seeking_description
      )

    new_genres = Genres(name=genres)
    artist.genres.append(new_genres)

    db.session.add(artist)
    db.session.commit()
  except():
    error = True
    db.session.rollback()
  finally:
        db.session.close()
  if error:
    flash('An error occurred. Artist ' + data.name + ' could not be listed.')
  if not error:
    flash('Artist ' + request.form['name'] + ' was successfully listed!')
  return render_template('pages/home.html')

#  Delete Artist
#------------------------------------------------------------------

@app.route('/artists/<artist_id>/delete', methods=['DELETE'])
def delete_artist(artist_id):
  artist = Artist.query.get(artist_id)
  error = False
  artist_name = artist.name
  try:
    db.session.delete(artist)
    db.session.commit()
  except:
    error = True
    db.session.rollback()
  finally:
    db.session.close()
  if error:
    flash('An error occurred deleting artist' + artist_name)
  else:
    flash('Successfully removed artist ' + artist_name)
  return redirect(url_for('artists'))


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  shows = Show.query.all()
  data=[]

  for show in shows:
    data.append({
      "venue_id": show.venue.id,
      "venue_name": show.venue.name,
      "artist_id": show.artist.id,
      "artist_name": show.artist.name,
      "artist_image_link": show.artist.image_link,
      "start_time": show.start_time
    })
  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  form = ShowForm()

  artist_id = form.artist_id.data
  venue_id = form.venue_id.data
  start_time = form.start_time.data

  error=False
  try:
    show = Show(
      artist_id=artist_id, 
      venue_id=venue_id, 
      start_time=start_time)
    db.session.add(show)
    db.session.commit()
  except():
    error = True
    db.session.rollback()
  finally:
        db.session.close()
  if error:
    flash('An error occurred. Show could not be listed.')
  if not error:
    flash('Show was successfully listed!')
  return render_template('pages/home.html')

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''