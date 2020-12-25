from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import DateTime

db = SQLAlchemy()


class Genres(db.Model):
    __tablename__ = 'Genres'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120))

# For many-to-many relationship between Venue & Genre
# the Venue table is the parent since it is more important
genres_venue = db.Table('genres_venue',
    db.Column('genres_id', db.Integer, db.ForeignKey('Genres.id'), primary_key=True),
    db.Column('venue_id', db.Integer, db.ForeignKey('Venue.id'), primary_key=True)
)

# For many-to-many relationship between Artist & Genre
# the Artist table is the parent since it is more important
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

    #to connect with Genres table via association table
    genres = db.relationship('Genres', secondary=genres_venue, lazy='subquery',
        backref=db.backref('venue', lazy=True))
    #to connect with Show table via association table
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
    #to connect with Genres table via association table
    genres = db.relationship('Genres', secondary=genres_artist, lazy='subquery',
            backref=db.backref('artist', lazy=True))
    #to connect with Show table via association table
    shows = db.relationship('Show', backref='artist')
    def __repr__(self):
      return f'<Artist {self.id}, {self.name}>'


class Show(db.Model):
    __tablename__ = 'Show'

    id = db.Column(db.Integer, primary_key=True)
    start_time = db.Column(DateTime, nullable=False)
    # because it is one-to-many relationship, we need for just foreign key, not table
    venue_id = db.Column(db.Integer, db.ForeignKey('Venue.id'))
    artist_id = db.Column(db.Integer, db.ForeignKey('Artist.id'))
    def __repr__(self):
        return f'<Show {self.id} {self.start_time} artist_id={artist_id} venue_id={venue_id}>'