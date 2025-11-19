import 'package:flutter/material.dart';
import 'package:fluttertoast/fluttertoast.dart';

class ClubDetailPage extends StatelessWidget {
  const ClubDetailPage({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        elevation: 0,
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(24.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.center,
          children: [
            Container(
              height: 200,
              width: double.infinity,
              padding: const EdgeInsets.all(16.0),
              decoration: BoxDecoration(
                color: Colors.black,
                borderRadius: BorderRadius.circular(16.0),
              ),
              // --- ⬇️ UPDATED IMAGE TO MATCH THE CLICKABLE CLUB ⬇️ ---
              child: Image.asset('assets/images/club1.png'), // Club Banner
            ),
            const SizedBox(height: 24),
            const Text(
              'TMC : The Music Club',
              style: TextStyle(fontSize: 28, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 16),
            const Text(
              'Providing a platform to cultivate and exhibit talent, The Music Club is the fraternity of all the music lovers in Manipal University. It promotes music culture and instills a passion for music amongst the students.\n\nBeing one of the most prestigious and reputable cultural clubs of the university, it is the abode of all students who are willing to learn, perform, grow and network.',
              textAlign: TextAlign.center,
              style: TextStyle(fontSize: 16, color: Colors.grey, height: 1.5),
            ),
            const SizedBox(height: 32),
            const Text(
              'Connect with us :',
              style: TextStyle(fontSize: 18, fontWeight: FontWeight.w600),
            ),
            const SizedBox(height: 12),
            const Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Icon(Icons.camera_alt_outlined, size: 32), // Placeholder for Instagram
                SizedBox(width: 20),
                Icon(Icons.link, size: 32), // Placeholder for LinkedIn
                SizedBox(width: 20),
                Icon(Icons.facebook, size: 32), // Placeholder for Facebook
              ],
            )
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
                msg: "You are now a member!",
                toastLength: Toast.LENGTH_SHORT,
                gravity: ToastGravity.BOTTOM,
                backgroundColor: Colors.green,
                textColor: Colors.white,
                fontSize: 16.0
            );
          },
          child: const Text('Become a member', style: TextStyle(fontSize: 18)),
        ),
      ),
    );
  }
}