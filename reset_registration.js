// MongoDB Shell Commands to Reset Registration
// Replace 'YOUR_WA_ID' with your actual WhatsApp number (without +)

// 1. Connect to your MongoDB (replace with your connection string)
// mongo "your_mongo_connection_string"

// 2. Switch to your database
use your_database_name;

// 3. Find your user record first (to verify)
db.users.findOne({wa_id: "YOUR_WA_ID"});

// 4. Delete your user record
db.users.deleteOne({wa_id: "YOUR_WA_ID"});

// 5. Verify deletion
db.users.findOne({wa_id: "YOUR_WA_ID"}); // Should return null

// EXAMPLES:
// If your WhatsApp number is +60123456789, use:
// db.users.findOne({wa_id: "60123456789"});
// db.users.deleteOne({wa_id: "60123456789"});

// To delete ALL test registrations (be careful!):
// db.users.deleteMany({wa_id: {$regex: "^60123"}); // Deletes all numbers starting with 60123