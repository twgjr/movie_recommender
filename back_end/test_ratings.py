"""
Test script to verify rating storage and recommendation updates
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def print_section(title):
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)

def test_rating_storage():
    """Test that ratings are being stored correctly"""
    print_section("Test 1: Clear existing ratings")
    
    # Clear any existing ratings
    response = requests.delete(f"{BASE_URL}/api/ratings/clear")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    
    print_section("Test 2: Submit individual ratings")
    
    # Submit some likes
    test_ratings = [
        {"imdb_id": "0111161", "rating": 1.0, "title": "The Shawshank Redemption"},  # Like
        {"imdb_id": "0068646", "rating": 1.0, "title": "The Godfather"},  # Like
        {"imdb_id": "0468569", "rating": 0.0, "title": "The Dark Knight"},  # Dislike
        {"imdb_id": "0109830", "rating": 0.0, "title": "Forrest Gump"},  # Dislike
    ]
    
    for rating in test_ratings:
        response = requests.post(
            f"{BASE_URL}/api/ratings/submit",
            json={"imdb_id": rating["imdb_id"], "rating": rating["rating"]}
        )
        print(f"\n{rating['title']} ({'Like' if rating['rating'] >= 0.5 else 'Dislike'})")
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print(f"Response: {response.json()}")
        else:
            print(f"Error: {response.text}")
    
    print_section("Test 3: Get all stored ratings")
    
    response = requests.get(f"{BASE_URL}/api/ratings/all")
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"\nTotal Ratings: {data['total_ratings']}")
        print(f"Likes: {data['like_count']}")
        print(f"Dislikes: {data['dislike_count']}")
        print(f"\nLiked Movies:")
        for imdb_id, rating in data['likes'].items():
            print(f"  - {imdb_id}: {rating}")
        print(f"\nDisliked Movies:")
        for imdb_id, rating in data['dislikes'].items():
            print(f"  - {imdb_id}: {rating}")
    else:
        print(f"Error: {response.text}")
    
    print_section("Test 4: Get recommendations based on preferences")
    
    # Get recommendations using the stored preferences
    preferences = [
        {"imdb_id": "0111161", "rating": 1.0},
        {"imdb_id": "0068646", "rating": 1.0},
        {"imdb_id": "0468569", "rating": 0.0},
        {"imdb_id": "0109830", "rating": 0.0},
    ]
    
    response = requests.post(
        f"{BASE_URL}/api/recommendations/user-preferences",
        json={"preferences": preferences, "limit": 10}
    )
    
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        recommendations = response.json()
        print(f"\nReceived {len(recommendations)} recommendations:")
        for i, movie in enumerate(recommendations[:5], 1):
            print(f"{i}. {movie.get('Title', 'N/A')} ({movie.get('Year', 'N/A')})")
            print(f"   Genre: {movie.get('Genre', 'N/A')}")
            print(f"   IMDb ID: {movie.get('imdbID', 'N/A')}")
    else:
        print(f"Error: {response.text}")
    
    print_section("Test 5: Add one more rating and get updated recommendations")
    
    # Add another like
    response = requests.post(
        f"{BASE_URL}/api/ratings/submit",
        json={"imdb_id": "0137523", "rating": 1.0}  # Fight Club
    )
    print(f"\nAdding Fight Club as a like")
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        print(f"Response: {response.json()}")
    
    # Get updated recommendations
    preferences.append({"imdb_id": "0137523", "rating": 1.0})
    response = requests.post(
        f"{BASE_URL}/api/recommendations/user-preferences",
        json={"preferences": preferences, "limit": 10}
    )
    
    print(f"\nUpdated recommendations:")
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        recommendations = response.json()
        print(f"Received {len(recommendations)} recommendations:")
        for i, movie in enumerate(recommendations[:5], 1):
            print(f"{i}. {movie.get('Title', 'N/A')} ({movie.get('Year', 'N/A')})")
            print(f"   Genre: {movie.get('Genre', 'N/A')}")
    else:
        print(f"Error: {response.text}")

if __name__ == "__main__":
    try:
        # Check if server is running
        response = requests.get(f"{BASE_URL}/api/health")
        if response.status_code != 200:
            print("Error: Backend server is not running or not responding")
            exit(1)
        
        print("Backend server is running!")
        print(f"Health check: {response.json()}")
        
        # Run tests
        test_rating_storage()
        
        print("\n" + "="*60)
        print("  All tests completed!")
        print("="*60)
        
    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to backend server at", BASE_URL)
        print("Please make sure the server is running with: python main.py")
        exit(1)
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
