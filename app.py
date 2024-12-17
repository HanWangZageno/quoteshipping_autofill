from flask import Flask, request, jsonify, render_template_string
import requests
from abacusai import ApiClient
import webbrowser
from threading import Timer

app = Flask(__name__)

# Abacus AI configuration
api_key = 's2_771c05ba79d349f3ae6b62bbef3217ca'
deployment_id = 'bcc79e06e'
deployment_token = 'b76035fb833a4d8abae047a4b3c6bd42'

# Initialize the API client
client = ApiClient(api_key)

 # Dummy data for customers and suppliers
CUSTOMER_NAMES = []  
SUPPLIER_NAMES = []


# Function to fetch supplier names from Abacus AI
def get_customer_names_from_abacus():
    try:
        customer_name_query = """
        SELECT DISTINCT name as customer_name
        FROM gold_customers
        """
        # Execute the query and get the result as a DataFrame
        result = client.execute_feature_group_sql(customer_name_query)
        
        # Extract the names and clean them
        return [customer_name.strip() for customer_name in result['customer_name'].tolist() if isinstance(customer_name, str) and customer_name.strip()]
    except Exception as e:
        print(f"Error fetching customer names: {e}")
        return []

# Function to fetch supplier names from Abacus AI
def get_supplier_names_from_abacus():
    try:
        supplier_name_query = """
        SELECT DISTINCT name
        FROM gold_suppliers
        """
        # Execute the query and get the result as a DataFrame
        result = client.execute_feature_group_sql(supplier_name_query)
        
        # Extract the names and clean them
        return [name.strip() for name in result['name'].tolist() if isinstance(name, str) and name.strip()]
    except Exception as e:
        print(f"Error fetching supplier names: {e}")
        return []

# Fetch and update supplier names
CUSTOMER_NAMES = get_customer_names_from_abacus()
SUPPLIER_NAMES = get_supplier_names_from_abacus()

# Function to predict shipping cost
def predict_shipping_cost(data):
    try:
        result = client.predict(
            deployment_token=deployment_token,
            deployment_id=deployment_id,
            query_data=data
        )
        return result
    except Exception as e:
        print(f"Error predicting shipping cost: {e}")
        return None

# Endpoint for dynamic customer name suggestions
@app.route('/autocomplete/customers', methods=['GET'])
def autocomplete_customers():
    query = request.args.get('q', '').lower()
    suggestions = [name for name in CUSTOMER_NAMES if query in name.lower()]
    return jsonify(suggestions)

# Endpoint for dynamic supplier name suggestions
@app.route('/autocomplete/suppliers', methods=['GET'])
def autocomplete_suppliers():
    query = request.args.get('q', '').lower()
    suggestions = [name for name in SUPPLIER_NAMES if query in name.lower()]
    return jsonify(suggestions)

# Main route
@app.route('/', methods=['GET', 'POST'])
def index():
    shipping_fee = None
    shipping_cost = None

    if request.method == 'POST':
        customer_name = request.form['customer_name']
        supplier_name = request.form['supplier_name']
        supplier_country = request.form['supplier_country']

        data = {
            "customer_name": customer_name,
            "supplier_name": supplier_name,
            "supplier_country": supplier_country,
            "transaction_type": "reseller",
            "order_purchase_type": "quote",
            
        }

        prediction_result = predict_shipping_cost(data)

        if prediction_result:
            shipping_cost = prediction_result.get('shipping_cost', 0)
            shipping_fee = max(99.84, 1.25 * shipping_cost)

    # Inline HTML template
    template = """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Shipping Cost Predictor</title>
        </head>
        <body>
            <h1>Predict Shipping Cost</h1>
            <form id="predictForm" action="/predict" method="POST">
                <label for="customer_name">Customer Name:</label>
                <input type="text" id="customer_name" name="customer_name" list="customer_suggestions" autocomplete="off">
                <datalist id="customer_suggestions"></datalist> <!-- Suggestions will populate dynamically -->
                
                <label for="supplier_name">Supplier Name:</label>
                <input type="text" id="supplier_name" name="supplier_name" list="supplier_suggestions" autocomplete="off">
                <datalist id="supplier_suggestions"></datalist> <!-- Suggestions will populate dynamically -->
                
                <label for="supplier_country">Supplier Country:</label>
                <select id="supplier_country" name="supplier_country">
                    <option value="GB">GB</option>
                    <option value="US">US</option>
                    <option value="DE">DE</option>
                    <option value="BE">BE</option>
                    <option value="FR">FR</option>
                </select>
                
                <button type="submit">Predict Shipping Cost</button>
            </form>
        </body>
        </html>
    """
    return render_template_string(template, shipping_fee=shipping_fee, shipping_cost=shipping_cost)


if __name__ == '__main__':
    app.run(debug=True)
