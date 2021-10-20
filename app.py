from enum import unique
from operator import ne
from flask import Flask, request, jsonify, sessions 
from flask_sqlalchemy import SQLAlchemy

from flask_marshmallow import Marshmallow, fields
import os

# Init app
app = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))
# Database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/test.db'
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///" + \
    os.path.join(basedir, "db.sqlite")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
# Init db
db = SQLAlchemy(app)
ma = Marshmallow(app)


class LicenceSchema(ma.Schema):
    class Meta:
        fields = ('id', 'name')

licence_schema = LicenceSchema()
licences_schema = LicenceSchema(many=True)


class ProductSchema(ma.Schema):
    licences = ma.Nested(LicenceSchema, many=True)
    class Meta:
        fields = ('id', 'name', 'price', 'qty', 'licences')
 
product_schema = ProductSchema()
products_schema = ProductSchema(many=True)


licences = db.Table('licences',
                    db.Column('licence_id', db.Integer, db.ForeignKey(
                        'licence.id'), primary_key=True),
                    db.Column('product_id', db.Integer, db.ForeignKey(
                        'product.id'), primary_key=True)
                    )


class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, unique=True)
    price = db.Column(db.Float)
    qty = db.Column(db.Integer)
    licences = db.relationship('Licence', secondary=licences, lazy='subquery',
                               backref=db.backref('products', lazy=True))

    def __init__(self, name, price, qty):
        self.name = name
        self.price = price
        self.qty = qty
        # self.licences = licences


class Licence(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, unique=True)

    def __init__(self, name):
        self.name = name


@app.route('/product/', methods=['POST'])
def add_product():
    name = request.json['name']
    price = request.json['price']
    qty = request.json['qty']
    licences =request.json['licences']
    new_product = Product(name, price, qty)
    db.session.add(new_product)
    db.session.commit()

    if licences:
        for el in licences:
            license = Licence.query.get(el)
            new_product.licences.append(license)
            db.session.commit()

    return product_schema.jsonify(new_product)


@app.route('/product/', methods=['GET'])
def get_products():
    all_products = Product.query.all()
    result = products_schema.dump(all_products)
    return jsonify(result)


@app.route('/product_with_licences/', methods=['GET'])
def get_filter_products():
    all_products = (
        db.session.query(Product)
        .join(licences)
        .filter(licences.columns.licence_id.is_not(None)).all()
    )
    result = products_schema.dump(all_products)
    return jsonify(result)


@app.route('/product/<id>', methods=['GET'])
def get_product(id):
    product = Product.query.get(id)
    return product_schema.jsonify(product)


@app.route('/product/<id>', methods=['PUT'])
def update_product(id):
    product = Product.query.get(id)

    name = request.json['name']
    price = request.json['price']
    qty = request.json['qty']
    licences = request.json['licences']
    product.name = name
    product.price = price
    product.qty = qty
    product.licences = []
    db.session.commit()

    for el in licences:
        license = Licence.query.get(el)
        product.licences.append(license)
        db.session.commit()
    
    db.session.commit()
    return product_schema.jsonify(product)



@app.route('/licence/', methods=['POST'])
def add_licence():
    name = request.json['name']

    new_licence = Licence(name)
    db.session.add(new_licence)
    db.session.commit()

    return licence_schema.jsonify(new_licence)


if __name__ == '__main__':
    app.run(debug=True)
