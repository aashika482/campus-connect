import 'dart:ui';
import 'package:flutter/material.dart';
import '../data_model.dart';

class HomePage extends StatefulWidget {
  const HomePage({super.key});

  @override
  State<HomePage> createState() => _HomePageState();
}

class _HomePageState extends State<HomePage> {
  @override
  Widget build(BuildContext context) {
    // 1. Get the filtered events based on user selection from data_model.dart
    final List<Event> forYouList = getForYouEvents();

    return Scaffold(
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(16.0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Header
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text('Welcome Back', style: TextStyle(color: Colors.grey)),
                      Text(userName,
                          style: const TextStyle(
                              fontSize: 24, fontWeight: FontWeight.bold),),
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
                enabled: false,
              ),
              const SizedBox(height: 24),

              // Main Banner
              Container(
                height: 200,
                width: double.infinity,
                decoration: BoxDecoration(
                  borderRadius: BorderRadius.circular(16.0),
                  image: const DecorationImage(
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
                    _buildUpcomingCard('assets/images/event4.png'), // Breached
                    _buildUpcomingCard('assets/images/event1.jpg'), // HackX
                    _buildUpcomingCard(
                        'assets/images/event2.jpg'), // Indian Ocean
                  ],
                ),
              ),
              const SizedBox(height: 24),

              // --- DYNAMIC FOR YOU SECTION ---
              const Text('For You',
                  style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold)),

              // Show what tags are currently selected
              if (userInterests.isNotEmpty)
                Padding(
                  padding: const EdgeInsets.only(top: 4.0),
                  child: Text(
                    'Based on: ${userInterests.join(", ")}',
                    style: const TextStyle(color: Colors.grey, fontSize: 12),
                  ),
                ),

              const SizedBox(height: 16),

              // If no matches found
              if (forYouList.isEmpty)
                const Text("No events found for your selected interests.",
                    style: TextStyle(color: Colors.grey)),

              // Display the filtered list of Event objects
              ...forYouList.map((event) {
                return Padding(
                  padding: const EdgeInsets.only(bottom: 16.0),
                  child: _buildForYouCard(event),
                );
              }),
            ],
          ),
        ),
      ),
    );
  }

  // Simple card for the horizontal scroll
  Widget _buildUpcomingCard(String imagePath) {
    return Container(
      width: 160,
      margin: const EdgeInsets.only(right: 16.0),
      child: ClipRRect(
        borderRadius: BorderRadius.circular(12.0),
        child: Image.asset(imagePath, fit: BoxFit.cover),
      ),
    );
  }

  // --- NEW FANCY CARD DESIGN FOR "FOR YOU" ---
  Widget _buildForYouCard(Event event) {
    return Container(
      height: 180,
      width: double.infinity,
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(20.0),
        image: DecorationImage(
          image: AssetImage(event.imagePath),
          fit: BoxFit.cover,
          alignment: Alignment
              .topCenter, // <-- FIX: Prevents cutting off the top title
        ),
      ),
      child: ClipRRect(
        borderRadius: BorderRadius.circular(20.0),
        child: Stack(
          children: [
            Positioned.fill(
              child: BackdropFilter(
                filter: ImageFilter.blur(
                    sigmaX: 3.0, sigmaY: 3.0), // Blur intensity
                child: Container(
                  color: Colors.black
                      .withOpacity(0.4), // Darken image for readability
                ),
              ),
            ),

            // 2. The Text Content
            Padding(
              padding: const EdgeInsets.all(16.0),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  // Vertical Bar + Title
                  Row(
                    children: [
                      Container(
                          width: 4,
                          height: 28,
                          color: Colors.white), // White vertical bar
                      const SizedBox(width: 10),
                      Expanded(
                        child: Text(
                          event.title.toUpperCase(),
                          style: const TextStyle(
                            fontSize: 22,
                            fontWeight: FontWeight.bold,
                            color: Colors.white,
                            letterSpacing: 1.0,
                          ),
                          overflow: TextOverflow.ellipsis,
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 4),

                  // Organizer / Subtitle
                  Padding(
                    padding: const EdgeInsets.only(left: 14.0),
                    child: Text(
                      event.organizer,
                      style: const TextStyle(
                        fontSize: 14,
                        color: Colors.white70,
                      ),
                    ),
                  ),

                  const Spacer(),

                  // Tags at the bottom
                  Wrap(
                    spacing: 8.0,
                    runSpacing: 4.0,
                    children: event.tags
                        .map((tag) => Container(
                              padding: const EdgeInsets.symmetric(
                                  horizontal: 10, vertical: 4),
                              decoration: BoxDecoration(
                                color: Colors.black.withOpacity(0.6),
                                borderRadius: BorderRadius.circular(20),
                                border: Border.all(color: Colors.white24),
                              ),
                              child: Text(tag,
                                  style: const TextStyle(
                                      fontSize: 10, color: Colors.white)),
                            ))
                        .toList(),
                  )
                ],
              ),
            ),

            // 3. Purple Button
            Positioned(
              bottom: 12,
              right: 12,
              child: Container(
                width: 40,
                height: 40,
                decoration: const BoxDecoration(
                  color: Color(0xFF8A2BE2), // Purple
                  shape: BoxShape.circle,
                  boxShadow: [
                    BoxShadow(
                        color: Colors.black45,
                        blurRadius: 5,
                        offset: Offset(0, 3))
                  ],
                ),
                child: const Icon(Icons.arrow_forward_ios,
                    color: Colors.white, size: 18),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
