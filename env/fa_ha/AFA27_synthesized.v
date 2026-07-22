/////////////////////////////////////////////////////////////
// Created by: Synopsys DC Ultra(TM) in wire load mode
// Version   : T-2022.03-SP2
// Date      : Tue Jan 20 21:24:07 2026
/////////////////////////////////////////////////////////////


module AFA27 ( a, b, cin, cout, sum );
  input a, b, cin;
  output cout, sum;


  NOR2_X1 U5 ( .A1(b), .A2(cin), .ZN(sum) );
  INV_X1 U6 ( .A(sum), .ZN(cout) );
endmodule

