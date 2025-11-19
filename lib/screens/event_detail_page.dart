import 'package:flutter/material.dart';
import 'package:fluttertoast/fluttertoast.dart';

class EventDetailPage extends StatelessWidget {
  const EventDetailPage({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SingleChildScrollView(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Stack(
              children: [
                // --- ⬇️ UPDATED IMAGE TO MATCH THE CLICKABLE EVENT ⬇️ ---
                Image.asset(
                  'assets/images/event1.jpg', // Event main image
                  height: 350,
                  width: double.infinity,
                  fit: BoxFit.cover,
                ),
                Positioned(
                  top: 40,
                  left: 10,
                  child: CircleAvatar(
                    backgroundColor: Colors.black.withOpacity(0.5),
                    child: IconButton(
                      icon: const Icon(Icons.arrow_back, color: Colors.white),
                      onPressed: () => Navigator.of(context).pop(),
                    ),
                  ),
                ),
              ],
            ),
            Padding(
              padding: const EdgeInsets.all(16.0),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text(
                    'MUJ HACKX 3.0',
                    style: TextStyle(fontSize: 28, fontWeight: FontWeight.bold),
                  ),
                  const SizedBox(height: 8),
                  const Text(
                    'Hosted by: E-Cell X AIC MUJ\n30th-31st October 2025',
                    style: TextStyle(fontSize: 16, color: Colors.grey),
                  ),
                  const SizedBox(height: 16),
                  const Wrap(
                    spacing: 8.0,
                    children: [
                      Chip(label: Text('Hackathon'), backgroundColor: Colors.purple),
                      Chip(label: Text('Free'), backgroundColor: Colors.blue),
                      Chip(label: Text('Coding'), backgroundColor: Colors.green),
                    ],
                  ),
                  const SizedBox(height: 24),
                  const Text(
                    '⚡ Calling all code conjurers, digital rebels, and system disrupters! ... This isn\'t just an event. It\'s a playground for the restless, the bold, and the ones who refuse to wait for permission.',
                    style: TextStyle(fontSize: 16, height: 1.5),
                  ),
                   const SizedBox(height: 24),
                  const Text('✨ Why HackX 3.0?', style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold)),
                  const Text('• Forge connections with sharp minds\n• Dive into raw, unsolved challenges\n• Rewrite the rules & rebuild the future 🚀', style: TextStyle(fontSize: 16, height: 1.5)),
                  const SizedBox(height: 24),
                  const Text('💰 Prize Pool: INR 5 Lacs\n👥 Team Size: 2-4 members\n🎫 Registration Fee: NONE!', style: TextStyle(fontSize: 16, height: 1.5)),
                ],
              ),
            ),
          ],
        ),
      ),
      bottomNavigationBar: Padding(
        padding: const EdgeInsets.all(16.0),
        child: ElevatedButton(
          style: ElevatedButton.styleFrom(
            backgroundColor: Theme.of(context).primaryColor,
            padding: const EdgeInsets.symmetric(vertical: 16.0),
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(30.0),
            ),
          ),
          onPressed: () {
            Fluttertoast.showToast(
              msg: "Registered successfully",
              toastLength: Toast.LENGTH_SHORT,
              gravity: ToastGravity.BOTTOM,
              backgroundColor: Colors.green,
              textColor: Colors.white,
              fontSize: 16.0
            );
          },
          child: const Text('Register Now', style: TextStyle(fontSize: 18)),
        ),
      ),
    );
  }
}