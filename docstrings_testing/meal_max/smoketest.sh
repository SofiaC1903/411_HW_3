#!/bin/bash

# Define the base URL for the Flask API
BASE_URL="http://localhost:5000/api"

# Flag to control whether to echo JSON output
ECHO_JSON=false

# Parse command-line arguments
while [ "$#" -gt 0 ]; do
  case $1 in
    --echo-json) ECHO_JSON=true ;;
    *) echo "Unknown parameter passed: $1"; exit 1 ;;
  esac
  shift
done


###############################################
#
# Health checks
#
###############################################

# Function to check the health of the service
check_health() {
  echo "Checking health status..."
  curl -s -X GET "$BASE_URL/health" | grep -q '"status": "healthy"'
  if [ $? -eq 0 ]; then
    echo "Service is healthy."
  else
    echo "Health check failed."
    exit 1
  fi
}

# Function to check the database connection
check_db() {
  echo "Checking database connection..."
  curl -s -X GET "$BASE_URL/db-check" | grep -q '"database_status": "healthy"'
  if [ $? -eq 0 ]; then
    echo "Database connection is healthy."
  else
    echo "Database check failed."
    exit 1
  fi
}


##########################################################
#
# Meal Management
#
##########################################################

clear_catalog() {
  echo "Clearing the catalog..."
  curl -s -X DELETE "$BASE_URL/clear-meals" | grep -q '"status": "success"'
}

create_meal() {
  meal=$1
  cuisine=$2
  price=$3
  difficulty=$4

  echo "Adding meal ($meal - $cuisine, $price) to the meal class..."
  response=$(curl -s -X POST "$BASE_URL/create-meal" -H "Content-Type: application/json" -d "{\"meal\":\"$meal\", \"cuisine\":$cuisine, \"price\":\"$price\", \"difficulty\":$difficulty\"}"| grep -q '"status": "success"')

  #http_code="${response: -3}"
  #body="${response:0:${#response}-3}"
    #echo "RESPONSE\" $response \"."
  echo "$body" | grep -q '"status": "success"'
  echo $response 
  if [[ $$ -eq 0 ]]; then
    echo "Meal added successfully."
  else
    echo "Failed to add meal."
    exit 1
  fi
}

delete_meal(){
  meal_id=$1

  echo "Deleting meal by ID ($meal_id)..."
  response=$(curl -s -X DELETE "$BASE_URL/delete-meal/$meal_id")
  echo $response
  if echo "$response" | grep -q '"status": "success"'; then
    echo "Meal deleted successfully by ID ($meal_id)."
  else
    echo "Failed to delete meal by ID ($meal_id)."
    exit 1
  fi
}

get_leaderboard() {
  echo "Getting leaderboard of meals..."
  response=$(curl -s -X GET "$BASE_URL/leaderboard")
  if echo "$response" | grep -q '"status": "success"'; then
    echo "Meal leaderboard retrieved successfully."
    if [ "$ECHO_JSON" = true ]; then
      echo "Leaderboard JSON:"
      echo "$response" | jq .
    fi
  else
    echo "Failed to get leaderboard."
    exit 1
  fi
}

get_meal_by_id() {
  meal_id=$1

  echo "Getting meal by ID ($meal_id)..."
  response=$(curl -s -X GET "$BASE_URL/get-meal-by-id/$meal_id")
  if echo "$response" | grep -q '"status": "success"'; then
    echo "Meal retrieved successfully by ID ($meal_id)."
    if [ "$ECHO_JSON" = true ]; then
      echo "Meal JSON (ID $meal_id):"
      echo "$response" | jq .
    fi
  else
    echo "Failed to get meal by ID ($meal_id)."
    exit 1
  fi
}

get_meal_by_name() {
  meal_name=$1

  echo "Getting meal by name (Meal: '$meal_name')..."
  response=$(curl -s -X GET "$BASE_URL/get-meal-by-name?meal_name=$(echo $meal_name | sed 's/ /%20/g')")
  if echo "$response" | grep -q '"status": "success"'; then
    echo "Meal retrieved successfully by name."
    if [ "$ECHO_JSON" = true ]; then
      echo "Meal JSON (by name):"
      echo "$response" | jq .
    fi
  else
    echo "Failed to get meal by name."
    exit 1
  fi
}

############################################################
#
# Battle Management
#
############################################################

battle() {
  echo "Initiating battle between two meals..."
  response=$(curl -s -X GET "$BASE_URL/battle" \
    -H "Content-Type: application/json" \
    )

  if echo "$response" | grep -q '"status": "success"'; then
    echo "Initiated battle successfully"
  else
    echo "Failed to initiate battle."
    exit 1
  fi
}

clear_combatants() {
  echo "Clearing combatants..."
  response=$(curl -s -X POST "$BASE_URL/clear-combatants")

  if echo "$response" | grep -q '"status": "success"'; then
    echo "Combatants list cleared successfully."
  else
    echo "Failed to clear combatants list."
    exit 1
  fi
}

get_combatants() {
  echo "Getting list of combatants participating in battle..."
  response=$(curl -s -X GET "$BASE_URL/get-combatants" \
    -H "Content-Type: application/json" \
   )

  if echo "$response" | grep -q '"status": "success"'; then
    echo "List of combatants retrieved successfully."
    if [ "$ECHO_JSON" = true ]; then
      echo "Combatants JSON:"
      echo "$response" | jq .
    fi
  else
    echo "Failed to retrieve list of combatants."
    exit 1
  fi
}

prep_combatant() {
  echo "Preparing a meal to becoma a combatant in battle..."
  response=$(curl -s -X POST "$BASE_URL/prep-combatant")

  if echo "$response" | grep -q '"status":'; then
    echo "Prepared combatant successfully."
  else
    echo "Failed to prepare combatant"
    exit 1
  fi
}

# Health checks
check_health
check_db

# Clear the catalog
clear_catalog

# Create songs
create_meal "Casserole" "American" 8.99 "HIGH" 
create_meal "Lasagna" "Italian" 12.99 "LOW" 
create_meal "Tacos Al Pastor" "Mexican" 9.99 "HIGH" 
create_meal "Fish Sticks" "American" 5.99 "LOW" 
create_meal "Chicken Quesadillas" "Mexican" 10.99 "MED" 

delete_meal 1
get_leaderboard

get_meal_by_id 2
get_meal_by_id 4
get_meal_by_name "Casserole"
get_meal_by_name "Fish Sticks"

battle

prep_combatant
get_combatants
clear_combatants

echo "All tests passed successfully!"
