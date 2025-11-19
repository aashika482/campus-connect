import 'package:flutter/material.dart';

class HomePage extends StatelessWidget {
  const HomePage({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(16.0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Welcome Header
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  const Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text('Welcome Back',
                          style: TextStyle(color: Colors.grey)),
                      Text('Aashika M',
                          style: TextStyle(
                              fontSize: 24, fontWeight: FontWeight.bold)),
                    ],
                  ),
                  CircleAvatar(
                    radius: 28,
                    backgroundColor: Theme.of(context).primaryColor,
                    child:
                        const Icon(Icons.person, size: 32, color: Colors.white),
                  ),
                ],
              ),
              const SizedBox(height: 24),

              // Search Bar
              TextField(
                decoration: InputDecoration(
                  hintText: 'Search for Events/Clubs...',
                  prefixIcon: const Icon(Icons.search),
                  filled: true,
                  fillColor: Colors.grey[850],
                  border: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(30.0),
                    borderSide: BorderSide.none,
                  ),
                ),
                enabled: false, // Non-functional as requested
              ),
              const SizedBox(height: 24),

              // Main Banner
              Container(
                height: 200,
                width: double.infinity,
                decoration: BoxDecoration(
                  borderRadius: BorderRadius.circular(16.0),
                  image: const DecorationImage(
                    // --- ⬇️ 1. MAIN BANNER IMAGE UPDATED HERE ⬇️ ---
                    image: AssetImage('assets/images/membership_drive.png'),
                    fit: BoxFit.cover,
                  ),
                ),
              ),
              const SizedBox(height: 24),

              // Upcoming Events Section
              const Text('Upcoming Events',
                  style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold)),
              const SizedBox(height: 16),
              SizedBox(
                height: 220,
                child: ListView(
                  scrollDirection: Axis.horizontal,
                  children: [
                    // --- ⬇️ 2. UPCOMING EVENT IMAGES UPDATED HERE ⬇️ ---
                    _buildEventCard('assets/images/breached.png'),
                    _buildEventCard('assets/images/hackx.jpg'),
                    _buildEventCard('assets/images/ind.jpg'),
                  ],
                ),
              ),
              const SizedBox(height: 24),

              // For You Section
              const Text('For You',
                  style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold)),
              const Text('Events curated just for you',
                  style: TextStyle(color: Colors.grey)),
              const SizedBox(height: 16),
              // --- ⬇️ 3. FOR YOU IMAGES UPDATED HERE ⬇️ ---
              _buildForYouCard('assets/images/foryou1.jpg'),
              const SizedBox(height: 12),
              _buildForYouCard('assets/images/foryou2.jpg'),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildEventCard(String imagePath) {
    return Container(
      width: 160,
      margin: const EdgeInsets.only(right: 16.0),
      child: ClipRRect(
        borderRadius: BorderRadius.circular(12.0),
        child: Image.asset(imagePath, fit: BoxFit.cover),
      ),
    );
  }

  Widget _buildForYouCard(String imagePath) {
    return Container(
      height: 150,
      width: double.infinity,
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(16.0),
        image: DecorationImage(
          image: AssetImage(imagePath),
          fit: BoxFit.cover,
        ),
      ),
    );
  }
}
