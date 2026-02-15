import 'package:flutter/material.dart';
import 'club_detail_page.dart';

class AllClubsPage extends StatelessWidget {
  const AllClubsPage({super.key});

  // --- ⬇️ UPDATED LIST WITH YOUR 12 CLUB LOGOS ⬇️ ---
  final List<String> clubLogos = const [
    'assets/images/club1.png', 
    'assets/images/club2.png',
    'assets/images/club3.png',
    'assets/images/club4.png',
    'assets/images/club5.png',
    'assets/images/club6.png',
    'assets/images/club7.png',
    'assets/images/club8.png',
    'assets/images/club9.png',
    'assets/images/club10.png',
    'assets/images/club11.png',
    'assets/images/club12.png',
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Browse all clubs'),
        backgroundColor: Colors.transparent,
        elevation: 0,
      ),
      body: Padding(
        padding: const EdgeInsets.all(16.0),
        child: GridView.builder(
          gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
            crossAxisCount: 3, // Shows 3 clubs per row
            crossAxisSpacing: 16.0,
            mainAxisSpacing: 16.0,
          ),
          itemCount: clubLogos.length,
          itemBuilder: (context, index) {
            Widget clubWidget = Container(
              padding: const EdgeInsets.all(8.0),
              decoration: BoxDecoration(
                color: Colors.grey[850],
                borderRadius: BorderRadius.circular(12.0),
              ),
              child: Image.asset(clubLogos[index], fit: BoxFit.contain),
            );

            // Only the first item is clickable
            if (index == 0) {
              return GestureDetector(
                onTap: () {
                  Navigator.push(
                    context,
                    MaterialPageRoute(builder: (context) => const ClubDetailPage()),
                  );
                },
                child: clubWidget,
              );
            } else {
              return clubWidget;
            }
          },
        ),
      ),
    );
  }
}