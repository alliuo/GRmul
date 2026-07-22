/////////////////////////////////////////////////////////////
// Created by: Synopsys DC Ultra(TM) in wire load mode
// Version   : T-2022.03-SP2
// Date      : Tue Jan 20 21:15:29 2026
/////////////////////////////////////////////////////////////


module AFA20 ( a, b, cin, cout, sum );
  input a, b, cin;
  output cout, sum;

  assign cout = 1'b0;

  OR3_X1 U5 ( .A1(b), .A2(cin), .A3(a), .ZN(sum) );
endmodule

