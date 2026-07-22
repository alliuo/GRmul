/////////////////////////////////////////////////////////////
// Created by: Synopsys DC Ultra(TM) in wire load mode
// Version   : T-2022.03-SP2
// Date      : Tue Jan 20 21:27:47 2026
/////////////////////////////////////////////////////////////


module AFA30 ( a, b, cin, cout, sum );
  input a, b, cin;
  output cout, sum;
  wire   cin;
  assign cout = cin;

  INV_X1 U3 ( .A(cin), .ZN(sum) );
endmodule

