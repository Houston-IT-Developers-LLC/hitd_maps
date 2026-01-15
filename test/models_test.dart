import 'package:flutter_test/flutter_test.dart';
import 'package:hitd_maps/src/models/parcel_info.dart';
import 'package:hitd_maps/src/models/public_land_info.dart';

void main() {
  group('ParcelInfo', () {
    group('fromProperties', () {
      test('parses standard property names', () {
        final properties = {
          'owner_name': 'John Doe',
          'situs_addr': '123 Main St',
          'county': 'Travis',
          'acreage': 10.5,
          'total_market_val': 250000,
          'parcel_id': 'ABC123',
        };

        final parcel = ParcelInfo.fromProperties(properties);

        expect(parcel.ownerName, equals('John Doe'));
        expect(parcel.address, equals('123 Main St'));
        expect(parcel.county, equals('Travis'));
        expect(parcel.acreage, equals(10.5));
        expect(parcel.marketValue, equals(250000));
        expect(parcel.parcelId, equals('ABC123'));
      });

      test('parses alternate property names (uppercase)', () {
        final properties = {
          'OWNER': 'Jane Smith',
          'ADDRESS': '456 Oak Ave',
          'COUNTY': 'Harris',
          'ACRES': 5.0,
          'MARKET_VALUE': 150000,
          'PARCEL_NO': 'XYZ789',
        };

        final parcel = ParcelInfo.fromProperties(properties);

        expect(parcel.ownerName, equals('Jane Smith'));
        expect(parcel.address, equals('456 Oak Ave'));
        expect(parcel.county, equals('Harris'));
        expect(parcel.acreage, equals(5.0));
        expect(parcel.marketValue, equals(150000));
        expect(parcel.parcelId, equals('XYZ789'));
      });

      test('handles missing properties', () {
        final properties = <String, dynamic>{};

        final parcel = ParcelInfo.fromProperties(properties);

        expect(parcel.ownerName, isNull);
        expect(parcel.address, isNull);
        expect(parcel.county, isNull);
        expect(parcel.acreage, isNull);
        expect(parcel.marketValue, isNull);
      });

      test('handles string acreage', () {
        final properties = {
          'acreage': '25.75',
        };

        final parcel = ParcelInfo.fromProperties(properties);

        expect(parcel.acreage, equals(25.75));
      });

      test('handles string market value', () {
        final properties = {
          'total_market_val': '500000',
        };

        final parcel = ParcelInfo.fromProperties(properties);

        expect(parcel.marketValue, equals(500000));
      });
    });

    group('formattedAcreage', () {
      test('formats small acreage with 2 decimals', () {
        final parcel = ParcelInfo(acreage: 1.5);
        expect(parcel.formattedAcreage, equals('1.50 acres'));
      });

      test('formats large acreage with 1 decimal', () {
        final parcel = ParcelInfo(acreage: 150.5);
        expect(parcel.formattedAcreage, equals('150.5 acres'));
      });

      test('returns null when acreage is null', () {
        final parcel = ParcelInfo();
        expect(parcel.formattedAcreage, isNull);
      });
    });

    group('formattedMarketValue', () {
      test('formats value in thousands', () {
        final parcel = ParcelInfo(marketValue: 250000);
        expect(parcel.formattedMarketValue, equals('\$250K'));
      });

      test('formats value in millions', () {
        final parcel = ParcelInfo(marketValue: 1500000);
        expect(parcel.formattedMarketValue, equals('\$1.5M'));
      });

      test('formats small values', () {
        final parcel = ParcelInfo(marketValue: 500);
        expect(parcel.formattedMarketValue, equals('\$500'));
      });

      test('returns null when value is null', () {
        final parcel = ParcelInfo();
        expect(parcel.formattedMarketValue, isNull);
      });
    });

    group('toJson/fromJson', () {
      test('round-trips correctly', () {
        final original = ParcelInfo(
          ownerName: 'Test Owner',
          address: '123 Test St',
          county: 'Test County',
          acreage: 50.5,
          marketValue: 300000,
          parcelId: 'TEST123',
        );

        final json = original.toJson();
        final restored = ParcelInfo.fromJson(json);

        expect(restored.ownerName, equals(original.ownerName));
        expect(restored.address, equals(original.address));
        expect(restored.county, equals(original.county));
        expect(restored.acreage, equals(original.acreage));
        expect(restored.marketValue, equals(original.marketValue));
        expect(restored.parcelId, equals(original.parcelId));
      });
    });
  });

  group('PublicLandInfo', () {
    group('fromProperties', () {
      test('parses PAD-US property names', () {
        final properties = {
          'Unit_Nm': 'Sam Houston National Forest',
          'Mang_Name': 'USFS',
          'Mang_Type': 'FED',
          'Des_Tp': 'NF',
          'GAP_Sts': '1',
          'GIS_Acres': 163000.5,
        };

        final land = PublicLandInfo.fromProperties(properties);

        expect(land.name, equals('Sam Houston National Forest'));
        expect(land.manager, equals('USFS'));
        expect(land.managerType, equals('FED'));
        expect(land.designation, equals('NF'));
        expect(land.gapStatus, equals('1'));
        expect(land.acres, equals(163000.5));
      });

      test('parses alternate property names', () {
        final properties = {
          'NAME': 'Test Area',
          'AGENCY': 'BLM',
          'TYPE': 'FED',
          'ACRES': 5000.0,
        };

        final land = PublicLandInfo.fromProperties(properties);

        expect(land.name, equals('Test Area'));
        expect(land.manager, equals('BLM'));
      });
    });

    group('landType', () {
      test('identifies BLM lands', () {
        final land = PublicLandInfo(manager: 'BLM');
        expect(land.landType, equals(PublicLandType.blm));
      });

      test('identifies National Forest', () {
        final land = PublicLandInfo(manager: 'USFS');
        expect(land.landType, equals(PublicLandType.nationalForest));
      });

      test('identifies National Park', () {
        final land = PublicLandInfo(manager: 'NPS');
        expect(land.landType, equals(PublicLandType.nationalPark));
      });

      test('identifies Fish and Wildlife', () {
        final land = PublicLandInfo(manager: 'FWS');
        expect(land.landType, equals(PublicLandType.fishAndWildlife));
      });

      test('identifies state lands', () {
        final land = PublicLandInfo(managerType: 'STAT');
        expect(land.landType, equals(PublicLandType.state));
      });

      test('returns other for unknown', () {
        final land = PublicLandInfo(manager: 'UNKNOWN');
        expect(land.landType, equals(PublicLandType.other));
      });
    });

    group('isHuntingAllowed', () {
      test('returns true for BLM', () {
        final land = PublicLandInfo(manager: 'BLM');
        expect(land.isHuntingAllowed, isTrue);
      });

      test('returns true for National Forest', () {
        final land = PublicLandInfo(manager: 'USFS');
        expect(land.isHuntingAllowed, isTrue);
      });

      test('returns false for National Park', () {
        final land = PublicLandInfo(manager: 'NPS');
        expect(land.isHuntingAllowed, isFalse);
      });

      test('returns true for state lands', () {
        final land = PublicLandInfo(managerType: 'STAT');
        expect(land.isHuntingAllowed, isTrue);
      });
    });

    group('formattedAcres', () {
      test('formats large acreage in thousands', () {
        final land = PublicLandInfo(acres: 163000);
        expect(land.formattedAcres, equals('163.0K acres'));
      });

      test('formats small acreage', () {
        final land = PublicLandInfo(acres: 500);
        expect(land.formattedAcres, equals('500 acres'));
      });
    });

    group('toJson/fromJson', () {
      test('round-trips correctly', () {
        final original = PublicLandInfo(
          name: 'Test Forest',
          manager: 'USFS',
          managerType: 'FED',
          designation: 'NF',
          gapStatus: '2',
          acres: 50000.0,
        );

        final json = original.toJson();
        final restored = PublicLandInfo.fromJson(json);

        expect(restored.name, equals(original.name));
        expect(restored.manager, equals(original.manager));
        expect(restored.managerType, equals(original.managerType));
        expect(restored.designation, equals(original.designation));
        expect(restored.gapStatus, equals(original.gapStatus));
        expect(restored.acres, equals(original.acres));
      });
    });
  });

  group('PublicLandType', () {
    test('all types have display names', () {
      for (final type in PublicLandType.values) {
        expect(type.displayName, isNotEmpty);
      }
    });

    test('all types have colors', () {
      for (final type in PublicLandType.values) {
        expect(type.color, isNotNull);
      }
    });
  });
}
