/////////////////////////////////////////////////////////////
// Created by: Synopsys DC Ultra(TM) in wire load mode
// Version   : T-2022.03-SP2
// Date      : Tue Jan 20 21:56:09 2026
/////////////////////////////////////////////////////////////


module AFA53 ( a, b, cin, cout, sum );
  input a, b, cin;
  output cout, sum;
  wire   b;
  assign cout = b;

  AND3_X1 U4 ( .A1(b), .A2(cin), .A3(a), .ZN(sum) );
endmodule

