#include <iostream>
#include <vector>
#include <fstream>
using namespace std;

struct date{
        int dat;
        int month;
        int year;
    };

class SymptomEntry
    {
private :
    date d;
    int severity;
    int temp;
    int humidity;
    int stress;
    float sleephrs;
    int activitylevel;

public:
    SymptomEntry(date dt, int sv, int t, int h, int st, float sh, int al)
    {
        d = dt;
        severity = sv;
        temp = t;
        humidity = h;
        stress = st;
        sleephrs = sh;
        activitylevel = al;
    }
    
   void display(int index)
    {
        cout << "Entry " << index << "\n";
        cout << "Date : " << d.dat << "/" << d.month << "/" << d.year
             << "\nSeverity : " << severity
             << "\nTemperature : " << temp
             << "\nHumidity : " << humidity
             << "\nStress : " << stress
             << "\nSleep : " << sleephrs
             << "\nActivity level : " << activitylevel << "\n";
    }
    };
    int check(const string &prompt, int low, int high)
    {
        int n;
        cout<<prompt;
        cin>>n;
        while(n<low || n>high)
        {
            cout<<"\nInvalid input\n"<<prompt<<"\n";
            cin>>n;
        }
        return n ;
    }

int main()
{
    fstream file;
    file.open("Hypertrackv1");
    vector<SymptomEntry> entries;
 
    int n = check("Enter 1 for entry of data , enter 0 if no more entries : ", 0, 1);
 
    while (n != 0)
    {
        date d;
        cout << "Enter date in the format date <space> month <space> year : ";
        cin >> d.dat >> d.month >> d.year;
 
        int sv = check("Enter severity of sweat in a scale from 1 to 10 : ", 1, 10);
 
        int humidity;
        cout << "Enter humidity : ";
        cin >> humidity;
 
        int stress;
        cout << "Enter stress : ";
        cin >> stress;
 
        int temp;
        cout << "Enter temperature in degree Celsius : ";
        cin >> temp;
 
        float sleephrs;
        cout << "Enter the time slept in hours : ";
        cin >> sleephrs;
 
        int activitylevel;
        cout << "Enter the activity level : ";
        cin >> activitylevel;
 
        entries.push_back(SymptomEntry(d, sv, temp, humidity, stress, sleephrs, activitylevel));
 
        n = check("Enter 1 for entry of data , enter 0 if no more entries : ", 0, 1);
    }
 
    for (int i = 0; i < entries.size(); i++)
    {
        entries[i].display(i + 1);
    }
 
    return 0;
}