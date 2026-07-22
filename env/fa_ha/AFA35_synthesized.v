/////////////////////////////////////////////////////////////
// Created by: Synopsys DC Ultra(TM) in wire load mode
// Version   : T-2022.03-SP2
// Date      : Tue Jan 20 21:33:57 2026
/////////////////////////////////////////////////////////////


module AFA35 ( a, b, cin, cout, sum );
  input a, b, cin;
  output cout, sum;
  wire   n7, n8, n9;

  INV_X1 U9 ( .A(a), .ZN(n8) );
  INV_X1 U10 ( .A(cin), .ZN(n7) );
  OAI221_X1 U11 ( .B1(a), .B2(cin), .C1(n8), .C2(n7), .A(b), .ZN(sum) );
  INV_X1 U12 ( .A(b), .ZN(n9) );
  AOI222_X1 U13 ( .A1(n9), .A2(n8), .B1(n9), .B2(n7), .C1(n8), .C2(n7), .ZN(
        cout) );
endmodule

