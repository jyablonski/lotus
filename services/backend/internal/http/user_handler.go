package http

import (
	"context"
	"database/sql"
	"encoding/json"
	"log"
	"net/http"
	"regexp"

	"github.com/jyablonski/lotus/internal/db"
	"github.com/jyablonski/lotus/internal/utils"

	"golang.org/x/crypto/bcrypt" // for password hashing
)

// regex to verify email format
var emailRegex = regexp.MustCompile(`^[a-z0-9]+@[a-z0-9]+\.[a-z]{2,}$`)

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
	email := r.URL.Query().Get("email")
	if email == "" {
		http.Error(w, "Missing email query parameter", http.StatusBadRequest)
		return
	}

	// query user from the database
	user, err := h.queries.GetUserByEmail(context.Background(), email)
	if err != nil {
		if err == sql.ErrNoRows {
			http.Error(w, "User not found", http.StatusNotFound)
			log.Printf("User %s not found", email)
		} else {
			http.Error(w, "Failed to retrieve user", http.StatusInternalServerError)
			log.Printf("Error retrieving user %s: %v", email, err)
		}
		return
	}

	// respond with user data
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	if err := json.NewEncoder(w).Encode(user); err != nil {
		http.Error(w, "Failed to encode response", http.StatusInternalServerError)
		log.Printf("Failed to encode user %s: %v", email, err)
	}
}

func (h *UserHandler) createUser(w http.ResponseWriter, r *http.Request) {
	log.Println("Received request to create user")

	// read in the request params
	var input db.CreateUserParams
	if err := json.NewDecoder(r.Body).Decode(&input); err != nil {
		log.Printf("Error decoding request body: %v\n", err)
		http.Error(w, "Invalid request body", http.StatusBadRequest)
		return
	}

	// validate the email format
	if !emailRegex.MatchString(input.Email) {
		log.Printf("Invalid email format: %s\n", input.Email)
		http.Error(w, "Invalid email format", http.StatusBadRequest)
		return
	}

	log.Printf("Creating user with email: %s\n", input.Email)

	// check if the email already exists in the database
	_, err := h.queries.GetUserByEmail(context.Background(), input.Email)
	if err == nil {
		// email already exists
		log.Printf("Email %s already exists\n", input.Email)
		http.Error(w, "Email already taken", http.StatusConflict)
		return
	} else if err != sql.ErrNoRows {
		// some other error occurred while querying the database
		log.Printf("Error checking email existence: %v\n", err)
		http.Error(w, "Error checking email availability", http.StatusInternalServerError)
		return
	}

	// validate the password
	if !input.Password.Valid || input.Password.String == "" {
		log.Println("Error: Password cannot be empty")
		http.Error(w, "Password cannot be empty", http.StatusBadRequest)
		return
	}

	// generate salt using utils.generateSalt
	salt, err := utils.GenerateSalt(24) // this creates a 32-character salt
	if err != nil {
		log.Printf("Error generating salt: %v\n", err)
		http.Error(w, "Failed to generate salt", http.StatusInternalServerError)
		return
	}

	saltedPassword := salt + input.Password.String // Concatenate salt and password

	// hash the concatenated password (salt + password)
	hashedPassword, err := bcrypt.GenerateFromPassword([]byte(saltedPassword), bcrypt.DefaultCost)
	if err != nil {
		log.Printf("Error hashing password: %v\n", err)
		http.Error(w, "Failed to hash password", http.StatusInternalServerError)
		return
	}

	// assign the salt and hashed password to the input
	input.Salt = sql.NullString{String: salt, Valid: true}
	input.Password = sql.NullString{String: string(hashedPassword), Valid: true}

	// create the user in the database
	user, err := h.queries.CreateUser(context.Background(), input)
	if err != nil {
		log.Printf("Error inserting user into database: %v\n", err)
		http.Error(w, "Failed to create user", http.StatusInternalServerError)
		return
	}

	log.Printf("Successfully created user: ID=%s, Email=%s\n", user.ID, user.Email)

	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusCreated)
	if err := json.NewEncoder(w).Encode(user); err != nil {
		log.Printf("Error encoding response: %v\n", err)
	}
}
