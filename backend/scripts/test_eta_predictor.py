from app.ai.ml.eta_predictor import predict_eta


features = {
    "shipping_mode": "Standard Class",
    "days_for_shipment_scheduled": 4,
    "order_item_quantity": 2,
    "product_price": 100.0,
    "customer_segment": "Consumer",
    "market": "US",
    "latitude": 35.7,
    "longitude": -80.3,
    "shipping_mode_delay_rate": 0.25,
}


eta = predict_eta(features)

print("Predicted ETA:", eta, "days")