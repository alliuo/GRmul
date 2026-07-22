/////////////////////////////////////////////////////////////
// Created by: Synopsys DC Ultra(TM) in wire load mode
// Version   : T-2022.03-SP2
// Date      : Tue Jan 20 21:26:33 2026
/////////////////////////////////////////////////////////////


module AFA29 ( a, b, cin, cout, sum );
  input a, b, cin;
  output cout, sum;


  OAI21_X1 U5 ( .B1(b), .B2(cin), .A(a), .ZN(sum) );
  INV_X1 U6 ( .A(sum), .ZN(cout) );
endmodule

