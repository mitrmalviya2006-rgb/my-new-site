// M'CHASHMA Eyewear - Store Information, Reviews & Zeiss Clinic Details

export const storeInfo = {
  name: "M'CHASHMA Eyewear",
  tagline: "Find frames that feel like you.",
  phone: "+91 98765 43210",
  whatsapp: "+91 98765 43210",
  email: "care@mchashma.in",
  hours: "Monday - Sunday: 10:30 AM - 9:30 PM",
  flagshipAddress: "Showroom #12-14, Central Promenade, Opp. City Center, Connaught Place, New Delhi 110001",
  locations: [
    {
      city: "New Delhi",
      name: "Flagship CP Experience Center",
      address: "Showroom #12-14, Central Promenade, Connaught Place",
      phone: "+91 98765 43210",
      hours: "10:30 AM - 9:30 PM (Open 7 Days)",
      hasZeissRefraction: true
    },
    {
      city: "Mumbai",
      name: "Bandra West Boutique",
      address: "Ground Floor, Linking Road, Near Waterfield Junction, Bandra West",
      phone: "+91 98765 43211",
      hours: "11:00 AM - 10:00 PM (Open 7 Days)",
      hasZeissRefraction: true
    },
    {
      city: "Bengaluru",
      name: "Indiranagar Studio",
      address: "100 Feet Road, 12th Main Corner, HAL 2nd Stage, Indiranagar",
      phone: "+91 98765 43212",
      hours: "10:30 AM - 9:30 PM (Open 7 Days)",
      hasZeissRefraction: true
    }
  ],
  amenities: [
    {
      icon: "eye",
      title: "Zeiss Digital Refraction Suite",
      description: "State-of-the-art subjective & objective refraction using calibrated Zeiss optometry equipment for 0.12D precision."
    },
    {
      icon: "clock",
      title: "30-Minute Express Lens Cutting",
      description: "In-store computer numeric lens edging lab. Walk in, choose your frames, and walk out with your finished spectacles."
    },
    {
      icon: "sparkles",
      title: "Ultrasonic Deep Cleansing & Tune-Up",
      description: "Free lifetime ultrasonic frame sterilization, screw tightening, nose pad replacement, and ear curve fitting."
    },
    {
      icon: "shield",
      title: "1-Year Unconditional Warranty",
      description: "Complete coverage on frame coating, hinge breakage, and accidental lens scratches within 12 months."
    }
  ],
  reviews: [
    {
      id: "rev-1",
      name: "Aakash Verma",
      city: "New Delhi",
      rating: 5,
      date: "September 2026",
      avatar: "AV",
      text: "The store ambience is top tier! Bright white counters with those eye-catching yellow display racks. Got my Zeiss BlueProtect power glasses made in 35 minutes flat. The virtual try-on on their site gave me the exact fit before I visited."
    },
    {
      id: "rev-2",
      name: "Pooja Hegde-Deshmukh",
      city: "Mumbai",
      rating: 5,
      date: "August 2026",
      avatar: "PD",
      text: "Bought the Maverick 24K gold aviators during their 50% off sunglasses promotion. The polarization quality cuts blinding Mumbai glare completely. Superb packaging with hard magnetic leather case."
    },
    {
      id: "rev-3",
      name: "Rohan Iyer",
      city: "Bengaluru",
      rating: 5,
      date: "September 2026",
      avatar: "RI",
      text: "The SwitchMaster 2-in-1 convertible is a lifesaver for people with power like me. No more carrying two pairs of glasses! The magnetic sun clip snaps on securely even while driving."
    }
  ]
};
