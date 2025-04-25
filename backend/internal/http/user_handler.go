package http

import (
	"context"
	"database/sql"
	"encoding/json"
	"log"
	"net/http"

	"github.com/jyablonski/lotus/internal/db"
)

type UserHandler struct {
	queries *db.Queries
}

// NewUserHandler initializes the user handler with database queries
func NewUserHandler(q *db.Queries) *UserHandler {
	return &UserHandler{queries: q}
}

// ServeHTTP handles user-related requests
func (h *UserHandler) ServeHTTP(w http.ResponseWriter, r *http.Request) {
	switch r.Method {
	case http.MethodGet:
		h.getUser(w, r)
	case http.MethodPost:
		h.createUser(w, r)
	default:
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
	}
}

// getUser handles GET requests to retrieve user information
func (h *UserHandler) getUser(w http.ResponseWriter, r *http.Request) {
	username := r.URL.Query().Get("username")
	if username == "" {
		http.Error(w, "Missing username query parameter", http.StatusBadRequest)
		return
	}

	// Query user from the database
	user, err := h.queries.GetUserByUsername(context.Background(), username)
	if err != nil {
		if err == sql.ErrNoRows {
			http.Error(w, "User not found", http.StatusNotFound)
			log.Printf("User %s not found", username)
		} else {
			http.Error(w, "Failed to retrieve user", http.StatusInternalServerError)
			log.Printf("Error retrieving user %s: %v", username, err)
		}
		return
	}

	// Respond with user data
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	if err := json.NewEncoder(w).Encode(user); err != nil {
		http.Error(w, "Failed to encode response", http.StatusInternalServerError)
		log.Printf("Failed to encode user %s: %v", username, err)
	}
}

// createUser handles POST requests to create a new user
func (h *UserHandler) createUser(w http.ResponseWriter, r *http.Request) {
	log.Println("Received request to create user")

	var input db.CreateUserParams
	if err := json.NewDecoder(r.Body).Decode(&input); err != nil {
		log.Printf("Error decoding request body: %v\n", err)
		http.Error(w, "Invalid request body", http.StatusBadRequest)
		return
	}

	log.Printf("Creating user with username: %s\n", input.Username)

	// check if the username already exists in the database
	_, err := h.queries.GetUserByUsername(context.Background(), input.Username)
	if err == nil {
		// Username already exists
		log.Printf("Username %s already exists\n", input.Username)
		http.Error(w, "Username already taken", http.StatusConflict)
		return
	} else if err != sql.ErrNoRows {
		// Some other error occurred while querying the database
		log.Printf("Error checking username existence: %v\n", err)
		http.Error(w, "Error checking username availability", http.StatusInternalServerError)
		return
	}

	// Hash password and generate salt before storing (placeholder)
	if input.Password == "" {
		log.Println("Error: Password cannot be empty")
		http.Error(w, "Password cannot be empty", http.StatusBadRequest)
		return
	}

	// Create the user in the database
	user, err := h.queries.CreateUser(context.Background(), input)
	if err != nil {
		log.Printf("Error inserting user into database: %v\n", err)
		http.Error(w, "Failed to create user", http.StatusInternalServerError)
		return
	}

	log.Printf("Successfully created user: ID=%d, Username=%s, Email=%s\n", user.ID, user.Username, user.Email)

	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusCreated)
	if err := json.NewEncoder(w).Encode(user); err != nil {
		log.Printf("Error encoding response: %v\n", err)
	}
}
