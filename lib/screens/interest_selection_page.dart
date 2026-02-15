import 'package:flutter/material.dart';
import '../data_model.dart'; // Import our new data model
import 'main_screen.dart';

class InterestSelectionPage extends StatefulWidget {
  const InterestSelectionPage({super.key});

  @override
  State<InterestSelectionPage> createState() => _InterestSelectionPageState();
}

class _InterestSelectionPageState extends State<InterestSelectionPage> {
  // Available tags to choose from
  final List<String> categories = [
    'Tech',
    'Music',
    'Art',
    'Dance',
    'Coding',
    'Hackathon',
    'Concert',
    'Gaming',
    'Photography',
    'Robotics',
    'Design',
    'Cryptic Hunt',
    'Culture',
    'Treasure Hunt'
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text("What interests you?"),
        backgroundColor: Colors.transparent,
        elevation: 0,
      ),
      body: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              "Select topics to personalize your feed.",
              style: TextStyle(fontSize: 16, color: Colors.grey),
            ),
            const SizedBox(height: 24),

            // The Chip Grid
            Wrap(
              spacing: 10.0,
              runSpacing: 10.0,
              children: categories.map((category) {
                final isSelected = userInterests.contains(category);
                return FilterChip(
                  label: Text(category),
                  selected: isSelected,
                  selectedColor: const Color(0xFF8A2BE2),
                  checkmarkColor: Colors.white,
                  labelStyle: TextStyle(
                      color: isSelected ? Colors.white : Colors.white),
                  backgroundColor: Colors.grey[800],
                  onSelected: (bool selected) {
                    setState(() {
                      if (selected) {
                        userInterests.add(category);
                      } else {
                        userInterests.remove(category);
                      }
                    });
                  },
                );
              }).toList(),
            ),
            const Spacer(),

            // Continue Button
            SizedBox(
              width: double.infinity,
              height: 50,
              child: ElevatedButton(
                style: ElevatedButton.styleFrom(
                  backgroundColor: const Color(0xFF8A2BE2),
                  shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(12)),
                ),
                onPressed: () {
                  // Navigate to the Main App
                  Navigator.pushAndRemoveUntil(
                    context,
                    MaterialPageRoute(builder: (context) => const MainScreen()),
                    (route) => false, // Remove back button history
                  );
                },
                child: const Text("Finish Setup",
                    style: TextStyle(fontSize: 18, color: Colors.white)),
              ),
            ),
            const SizedBox(height: 24),
          ],
        ),
      ),
    );
  }
}
