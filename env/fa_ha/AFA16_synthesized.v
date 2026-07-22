/////////////////////////////////////////////////////////////
// Created by: Synopsys DC Ultra(TM) in wire load mode
// Version   : T-2022.03-SP2
// Date      : Tue Jan 20 21:10:33 2026
/////////////////////////////////////////////////////////////


module AFA16 ( a, b, cin, cout, sum );
  input a, b, cin;
  output cout, sum;
  wire   cin, n2;
  assign cout = cin;

  NOR2_X1 U5 ( .A1(a), .A2(b), .ZN(n2) );
  NOR2_X1 U6 ( .A1(cin), .A2(n2), .ZN(sum) );
endmodule

