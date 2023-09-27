from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

app = Flask(__name__)

# Replace 'mysql://user:password@localhost/database' with your MySQL database connection details.
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:ankita@localhost:3307/food_order_master'
db = SQLAlchemy(app)

migrate = Migrate(app, db)

# Define a model for menu items
class MenuItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(200))
    price = db.Column(db.Float, nullable=False)
    availability = db.Column(db.Boolean, default=True)

    def serialize(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'price': self.price,
            'availability': self.availability,
        }

# Define a model for orders
class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_name = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(50), default='received')
    items = db.relationship('MenuItem', secondary='order_menuitem', backref='orders')

    def serialize(self):
        return {
            'id': self.id,
            'customer_name': self.customer_name,
            'status': self.status,
            'items': [item.serialize() for item in self.items]
        }

# Define a many-to-many relationship table between orders and menu items
order_menuitem = db.Table(
    'order_menuitem',
    db.Column('order_id', db.Integer, db.ForeignKey('order.id'), primary_key=True),
    db.Column('menuitem_id', db.Integer, db.ForeignKey('menu_item.id'), primary_key=True)
)

# Route to list all menu items
@app.route('/menu', methods=['GET'])
def list_menu():
    menu_items = MenuItem.query.all()
    return jsonify([item.serialize() for item in menu_items])

# Route to add a new menu item
@app.route('/menu/add', methods=['POST'])
def add_menu_item():
    data = request.get_json()
    if 'name' in data and 'price' in data:
        new_item = MenuItem(
            name=data['name'],
            description=data.get('description', ''),
            price=data['price'],
            availability=data.get('availability', True)
        )
        db.session.add(new_item)
        db.session.commit()
        return jsonify(new_item.serialize()), 201
    return jsonify({'error': 'Invalid menu item data'}), 400

# Route to remove a menu item by ID
@app.route('/menu/remove/<int:item_id>', methods=['DELETE'])
def remove_menu_item(item_id):
    menu_item = MenuItem.query.get(item_id)
    if menu_item:
        db.session.delete(menu_item)
        db.session.commit()
        return jsonify({'message': f'Menu item "{menu_item.name}" removed successfully'}), 200
    else:
        return jsonify({'error': f'Menu item with ID {item_id} not found'}), 404

# Route to update the availability of a menu item by ID
@app.route('/menu/update_availability/<int:item_id>', methods=['PUT'])
def update_menu_item_availability(item_id):
    data = request.get_json()
    menu_item = MenuItem.query.get(item_id)
    if menu_item:
        new_availability = data.get('availability', True)
        menu_item.availability = new_availability
        db.session.commit()
        return jsonify({'message': f'Availability of "{menu_item.name}" updated successfully'}), 200
    else:
        return jsonify({'error': f'Menu item with ID {item_id} not found'}), 404
    
# Route to accept a new food order
@app.route('/order', methods=['POST'])
def take_order():
    data = request.get_json()
    customer_name = data.get('customer_name')
    dish_ids = data.get('dish_ids', [])

    order = Order(
        customer_name=customer_name,
        status='received',
    )

    for dish_id in dish_ids:
        # Check if the menu item exists and is available
        menu_item = MenuItem.query.get(dish_id)
        if menu_item and menu_item.availability:
            order.items.append(menu_item)
        else:
            return jsonify({'error': f'Menu item with ID {dish_id} is not available'}), 400

    db.session.add(order)
    db.session.commit()
    
    return jsonify(order.serialize()), 201

# Route to update the status of a food order by ID
@app.route('/order/update_status/<int:order_id>', methods=['PUT'])
def update_order_status(order_id):
    data = request.get_json()
    new_status = data.get('status')

    order = Order.query.get(order_id)
    if order:
        valid_statuses = ['received', 'preparing', 'ready for pickup', 'delivered']

        if new_status in valid_statuses:
            order.status = new_status
            db.session.commit()
            return jsonify({'message': f'Status of order {order_id} updated to "{new_status}"'}), 200
        else:
            return jsonify({'error': f'Invalid status: "{new_status}"'}), 400
    else:
        return jsonify({'error': f'Order with ID {order_id} not found'}), 404

# Route to review all food orders
@app.route('/orders/review', methods=['GET'])
def review_orders():
    orders = Order.query.all()
    return jsonify([order.serialize() for order in orders])


if __name__ == "__main__":
    app.run(debug=True)
