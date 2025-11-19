import 'package:flutter/material.dart';
import 'event_detail_page.dart';

class AllEventsPage extends StatelessWidget {
  const AllEventsPage({super.key});

  // --- ⬇️ UPDATED LIST OF YOUR EVENT IMAGES ⬇️ ---
  // The filenames and extensions match your folder exactly.
  final List<String> eventImages = const [
    'assets/images/event1.jpg', // This one will be clickable
    'assets/images/event2.jpg',
    'assets/images/event3.png',
    'assets/images/event4.png',
    'assets/images/event5.png',
    'assets/images/event6.png',
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Browse all events'),
        backgroundColor: Colors.transparent,
        elevation: 0,
      ),
      body: Padding(
        padding: const EdgeInsets.all(8.0),
        child: GridView.builder(
          gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
            crossAxisCount: 2,
            crossAxisSpacing: 10.0,
            mainAxisSpacing: 10.0,
            childAspectRatio: 0.7, // Adjust this ratio if images look stretched
          ),
          itemCount: eventImages.length,
          itemBuilder: (context, index) {
            // Only the first item is clickable as per the request
            if (index == 0) {
              return GestureDetector(
                onTap: () {
                  Navigator.push(
                    context,
                    MaterialPageRoute(builder: (context) => const EventDetailPage()),
                  );
                },
                child: ClipRRect(
                  borderRadius: BorderRadius.circular(12.0),
                  child: Image.asset(eventImages[index], fit: BoxFit.cover),
                ),
              );
            } else {
              // The rest are static images
              return ClipRRect(
                borderRadius: BorderRadius.circular(12.0),
                child: Image.asset(eventImages[index], fit: BoxFit.cover),
              );
            }
          },
        ),
      ),
    );
  }
}