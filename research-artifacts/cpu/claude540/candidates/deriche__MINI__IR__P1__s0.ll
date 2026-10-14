; ModuleID = 'kernel.c'
source_filename = "kernel.c"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

; Function Attrs: noinline nounwind uwtable
define dso_local void @kernel_deriche(i32 noundef %w, i32 noundef %h, float noundef %alpha, ptr noundef %imgIn, ptr noundef %imgOut, ptr noundef %y1, ptr noundef %y2) #0 {
entry:
  %wcmp = icmp sgt i32 %w, 0
  %hcmp = icmp sgt i32 %h, 0
  %w64 = sext i32 %w to i64
  %h64 = sext i32 %h to i64

  %fneg = fneg float %alpha
  %call = call float @expf(float noundef %fneg) #2
  %sub = fsub float 1.000000e+00, %call
  %call9 = call float @expf(float noundef %fneg) #2
  %sub10 = fsub float 1.000000e+00, %call9
  %mul = fmul float %sub, %sub10
  %mul11 = fmul float 2.000000e+00, %alpha
  %call13 = call float @expf(float noundef %fneg) #2
  %mul14 = fmul float %mul11, %call13
  %add15 = fadd float 1.000000e+00, %mul14
  %call17 = call float @expf(float noundef %mul11) #2
  %sub18 = fsub float %add15, %call17
  %k = fdiv float %mul, %sub18

  %a1 = %k
  %a5 = %k

  %call20 = call float @expf(float noundef %fneg) #2
  %mul21 = fmul float %k, %call20
  %sub22 = fsub float %alpha, 1.000000e+00
  %a2 = fmul float %mul21, %sub22
  %a6 = %a2

  %call25 = call float @expf(float noundef %fneg) #2
  %mul26 = fmul float %k, %call25
  %add27 = fadd float %alpha, 1.000000e+00
  %a3 = fmul float %mul26, %add27
  %a7 = %a3

  %fneg29 = fneg float %k
  %mul30 = fmul float -2.000000e+00, %alpha
  %call31 = call float @expf(float noundef %mul30) #2
  %a4 = fmul float %fneg29, %call31
  %a8 = %a4

  %call34 = call float @powf(float noundef 2.000000e+00, float noundef %fneg) #2
  %b1 = %call34

  %call36 = call float @expf(float noundef %mul30) #2
  %b2 = fneg float %call36

  %c1 = 1.000000e+00
  %c2 = 1.000000e+00

  br label %loop1.preheader

loop1.preheader:
  br i1 %wcmp, label %loop1.i.body, label %for.end64

loop1.i.body:
  %i1 = phi i64 [ 0, %loop1.preheader ], [ %i1.next, %loop1.i.inc ]
  %imgIn.row1 = getelementptr inbounds float, ptr %imgIn, i64 %i1
  %rowoff1 = mul nsw i64 %i1, %h64
  %imgIn.rowptr1 = getelementptr inbounds float, ptr %imgIn, i64 %rowoff1
  %y1.rowptr1 = getelementptr inbounds float, ptr %y1, i64 %rowoff1
  br i1 %hcmp, label %loop1.j.body.preheader, label %loop1.i.inc

loop1.j.body.preheader:
  br label %loop1.j.body

loop1.j.body:
  %j1 = phi i64 [ 0, %loop1.j.body.preheader ], [ %j1.next, %loop1.j.body ]
  %xm1.phi = phi float [ 0.000000e+00, %loop1.j.body.preheader ], [ %xcur1, %loop1.j.body ]
  %ym1.phi = phi float [ 0.000000e+00, %loop1.j.body.preheader ], [ %ycur1, %loop1.j.body ]
  %ym2.phi = phi float [ 0.000000e+00, %loop1.j.body.preheader ], [ %ym1.phi, %loop1.j.body ]

  %inptr1 = getelementptr inbounds float, ptr %imgIn.rowptr1, i64 %j1
  %xcur1 = load float, ptr %inptr1, align 4

  %m1a = fmul float %a1, %xcur1
  %m1b = fmul float %a2, %xm1.phi
  %s1a = fadd float %m1a, %m1b
  %m1c = fmul float %b1, %ym1.phi
  %s1b = fadd float %s1a, %m1c
  %m1d = fmul float %b2, %ym2.phi
  %ycur1 = fadd float %s1b, %m1d

  %outptr1 = getelementptr inbounds float, ptr %y1.rowptr1, i64 %j1
  store float %ycur1, ptr %outptr1, align 4

  %j1.next = add nsw i64 %j1, 1
  %j1done = icmp eq i64 %j1.next, %h64
  br i1 %j1done, label %loop1.i.inc, label %loop1.j.body

loop1.i.inc:
  %i1.next = add nsw i64 %i1, 1
  %i1done = icmp eq i64 %i1.next, %w64
  br i1 %i1done, label %for.end64, label %loop1.i.body

for.end64:
  br i1 %wcmp, label %loop2.i.body, label %for.end95

loop2.i.body:
  %i2 = phi i64 [ 0, %for.end64 ], [ %i2.next, %loop2.i.inc ]
  %rowoff2 = mul nsw i64 %i2, %h64
  %imgIn.rowptr2 = getelementptr inbounds float, ptr %imgIn, i64 %rowoff2
  %y2.rowptr2 = getelementptr inbounds float, ptr %y2, i64 %rowoff2
  br i1 %hcmp, label %loop2.j.body.preheader, label %loop2.i.inc

loop2.j.body.preheader:
  %hm1 = sub nsw i64 %h64, 1
  br label %loop2.j.body

loop2.j.body:
  %j2 = phi i64 [ %hm1, %loop2.j.body.preheader ], [ %j2.next, %loop2.j.body ]
  %xp1.phi = phi float [ 0.000000e+00, %loop2.j.body.preheader ], [ %xcur2, %loop2.j.body ]
  %xp2.phi = phi float [ 0.000000e+00, %loop2.j.body.preheader ], [ %xp1.phi, %loop2.j.body ]
  %yp1.phi = phi float [ 0.000000e+00, %loop2.j.body.preheader ], [ %ycur2, %loop2.j.body ]
  %yp2.phi = phi float [ 0.000000e+00, %loop2.j.body.preheader ], [ %yp1.phi, %loop2.j.body ]

  %m2a = fmul float %a3, %xp1.phi
  %m2b = fmul float %a4, %xp2.phi
  %s2a = fadd float %m2a, %m2b
  %m2c = fmul float %b1, %yp1.phi
  %s2b = fadd float %s2a, %m2c
  %m2d = fmul float %b2, %yp2.phi
  %ycur2 = fadd float %s2b, %m2d

  %outptr2 = getelementptr inbounds float, ptr %y2.rowptr2, i64 %j2
  store float %ycur2, ptr %outptr2, align 4

  %inptr2 = getelementptr inbounds float, ptr %imgIn.rowptr2, i64 %j2
  %xcur2 = load float, ptr %inptr2, align 4

  %j2eq0 = icmp eq i64 %j2, 0
  %j2.next = sub nsw i64 %j2, 1
  br i1 %j2eq0, label %loop2.i.inc, label %loop2.j.body

loop2.i.inc:
  %i2.next = add nsw i64 %i2, 1
  %i2done = icmp eq i64 %i2.next, %w64
  br i1 %i2done, label %for.end95, label %loop2.i.body

for.end95:
  br i1 %wcmp, label %loop3.i.body, label %for.end121

loop3.i.body:
  %i3 = phi i64 [ 0, %for.end95 ], [ %i3.next, %loop3.i.inc ]
  %rowoff3a = mul nsw i64 %i3, %h64
  %y1.rowptr3 = getelementptr inbounds float, ptr %y1, i64 %rowoff3a
  %y2.rowptr3 = getelementptr inbounds float, ptr %y2, i64 %rowoff3a
  %imgOut.rowptr3 = getelementptr inbounds float, ptr %imgOut, i64 %rowoff3a
  br i1 %hcmp, label %loop3.j.body.preheader, label %loop3.i.inc

loop3.j.body.preheader:
  br label %loop3.j.body

loop3.j.body:
  %j3 = phi i64 [ 0, %loop3.j.body.preheader ], [ %j3.next, %loop3.j.body ]
  %y1ptr3 = getelementptr inbounds float, ptr %y1.rowptr3, i64 %j3
  %y1v3 = load float, ptr %y1ptr3, align 4
  %y2ptr3 = getelementptr inbounds float, ptr %y2.rowptr3, i64 %j3
  %y2v3 = load float, ptr %y2ptr3, align 4
  %addv3 = fadd float %y1v3, %y2v3
  %mulv3 = fmul float %c1, %addv3
  %outptr3 = getelementptr inbounds float, ptr %imgOut.rowptr3, i64 %j3
  store float %mulv3, ptr %outptr3, align 4

  %j3.next = add nsw i64 %j3, 1
  %j3done = icmp eq i64 %j3.next, %h64
  br i1 %j3done, label %loop3.i.inc, label %loop3.j.body

loop3.i.inc:
  %i3.next = add nsw i64 %i3, 1
  %i3done = icmp eq i64 %i3.next, %w64
  br i1 %i3done, label %for.end121, label %loop3.i.body

for.end121:
  br i1 %hcmp, label %loop4.j.body, label %for.end156

loop4.j.body:
  %j4 = phi i64 [ 0, %for.end121 ], [ %j4.next, %loop4.i.inc ]
  br i1 %wcmp, label %loop4.i.body.preheader, label %loop4.i.inc

loop4.i.body.preheader:
  br label %loop4.i.body

loop4.i.body:
  %i4 = phi i64 [ 0, %loop4.i.body.preheader ], [ %i4.next, %loop4.i.body ]
  %tm1.phi = phi float [ 0.000000e+00, %loop4.i.body.preheader ], [ %tcur4, %loop4.i.body ]
  %ym1.phi4 = phi float [ 0.000000e+00, %loop4.i.body.preheader ], [ %ycur4, %loop4.i.body ]
  %ym2.phi4 = phi float [ 0.000000e+00, %loop4.i.body.preheader ], [ %ym1.phi4, %loop4.i.body ]

  %rowoff4 = mul nsw i64 %i4, %h64
  %imgOut.ptr4 = getelementptr inbounds float, ptr %imgOut, i64 %rowoff4
  %imgOut.ptr4j = getelementptr inbounds float, ptr %imgOut.ptr4, i64 %j4
  %tcur4 = load float, ptr %imgOut.ptr4j, align 4

  %m4a = fmul float %a5, %tcur4
  %m4b = fmul float %a6, %tm1.phi
  %s4a = fadd float %m4a, %m4b
  %m4c = fmul float %b1, %ym1.phi4
  %s4b = fadd float %s4a, %m4c
  %m4d = fmul float %b2, %ym2.phi4
  %ycur4 = fadd float %s4b, %m4d

  %y1.rowptr4 = getelementptr inbounds float, ptr %y1, i64 %rowoff4
  %y1.ptr4j = getelementptr inbounds float, ptr %y1.rowptr4, i64 %j4
  store float %ycur4, ptr %y1.ptr4j, align 4

  %i4.next = add nsw i64 %i4, 1
  %i4done = icmp eq i64 %i4.next, %w64
  br i1 %i4done, label %loop4.i.inc, label %loop4.i.body

loop4.i.inc:
  %j4.next = add nsw i64 %j4, 1
  %j4done = icmp eq i64 %j4.next, %h64
  br i1 %j4done, label %for.end156, label %loop4.j.body

for.end156:
  br i1 %hcmp, label %loop5.j.body, label %for.end188

loop5.j.body:
  %j5 = phi i64 [ 0, %for.end156 ], [ %j5.next, %loop5.i.inc ]
  br i1 %wcmp, label %loop5.i.body.preheader, label %loop5.i.inc

loop5.i.body.preheader:
  %wm1 = sub nsw i64 %w64, 1
  br label %loop5.i.body

loop5.i.body:
  %i5 = phi i64 [ %wm1, %loop5.i.body.preheader ], [ %i5.next, %loop5.i.body ]
  %tp1.phi = phi float [ 0.000000e+00, %loop5.i.body.preheader ], [ %tcur5, %loop5.i.body ]
  %tp2.phi = phi float [ 0.000000e+00, %loop5.i.body.preheader ], [ %tp1.phi, %loop5.i.body ]
  %yp1.phi5 = phi float [ 0.000000e+00, %loop5.i.body.preheader ], [ %ycur5, %loop5.i.body ]
  %yp2.phi5 = phi float [ 0.000000e+00, %loop5.i.body.preheader ], [ %yp1.phi5, %loop5.i.body ]

  %m5a = fmul float %a7, %tp1.phi
  %m5b = fmul float %a8, %tp2.phi
  %s5a = fadd float %m5a, %m5b
  %m5c = fmul float %b1, %yp1.phi5
  %s5b = fadd float %s5a, %m5c
  %m5d = fmul float %b2, %yp2.phi5
  %ycur5 = fadd float %s5b, %m5d

  %rowoff5 = mul nsw i64 %i5, %h64
  %y2.rowptr5 = getelementptr inbounds float, ptr %y2, i64 %rowoff5
  %y2.ptr5j = getelementptr inbounds float, ptr %y2.rowptr5, i64 %j5
  store float %ycur5, ptr %y2.ptr5j, align 4

  %imgOut.rowptr5 = getelementptr inbounds float, ptr %imgOut, i64 %rowoff5
  %imgOut.ptr5j = getelementptr inbounds float, ptr %imgOut.rowptr5, i64 %j5
  %tcur5 = load float, ptr %imgOut.ptr5j, align 4

  %i5eq0 = icmp eq i64 %i5, 0
  %i5.next = sub nsw i64 %i5, 1
  br i1 %i5eq0, label %loop5.i.inc, label %loop5.i.body

loop5.i.inc:
  %j5.next = add nsw i64 %j5, 1
  %j5done = icmp eq i64 %j5.next, %h64
  br i1 %j5done, label %for.end188, label %loop5.j.body

for.end188:
  br i1 %wcmp, label %loop6.i.body, label %for.end214

loop6.i.body:
  %i6 = phi i64 [ 0, %for.end188 ], [ %i6.next, %loop6.i.inc ]
  %rowoff6 = mul nsw i64 %i6, %h64
  %y1.rowptr6 = getelementptr inbounds float, ptr %y1, i64 %rowoff6
  %y2.rowptr6 = getelementptr inbounds float, ptr %y2, i64 %rowoff6
  %imgOut.rowptr6 = getelementptr inbounds float, ptr %imgOut, i64 %rowoff6
  br i1 %hcmp, label %loop6.j.body.preheader, label %loop6.i.inc

loop6.j.body.preheader:
  br label %loop6.j.body

loop6.j.body:
  %j6 = phi i64 [ 0, %loop6.j.body.preheader ], [ %j6.next, %loop6.j.body ]
  %y1ptr6 = getelementptr inbounds float, ptr %y1.rowptr6, i64 %j6
  %y1v6 = load float, ptr %y1ptr6, align 4
  %y2ptr6 = getelementptr inbounds float, ptr %y2.rowptr6, i64 %j6
  %y2v6 = load float, ptr %y2ptr6, align 4
  %addv6 = fadd float %y1v6, %y2v6
  %mulv6 = fmul float %c2, %addv6
  %outptr6 = getelementptr inbounds float, ptr %imgOut.rowptr6, i64 %j6
  store float %mulv6, ptr %outptr6, align 4

  %j6.next = add nsw i64 %j6, 1
  %j6done = icmp eq i64 %j6.next, %h64
  br i1 %j6done, label %loop6.i.inc, label %loop6.j.body

loop6.i.inc:
  %i6.next = add nsw i64 %i6, 1
  %i6done = icmp eq i64 %i6.next, %w64
  br i1 %i6done, label %for.end214, label %loop6.i.body

for.end214:
  ret void
}

; Function Attrs: nounwind
declare float @expf(float noundef) #1

; Function Attrs: nounwind
declare float @powf(float noundef, float noundef) #1

attributes #0 = { noinline nounwind uwtable "frame-pointer"="all" "min-legal-vector-width"="0" "no-trapping-math"="true" "stack-protector-buffer-size"="8" }
attributes #1 = { nounwind "frame-pointer"="all" "no-trapping-math"="true" "stack-protector-buffer-size"="8" }
attributes #2 = { nounwind }

!llvm.module.flags = !{!0, !1, !2, !3, !4}
!llvm.ident = !{!5}

!0 = !{i32 1, !"wchar_size", i32 4}
!1 = !{i32 8, !"PIC Level", i32 2}
!2 = !{i32 7, !"PIE Level", i32 2}
!3 = !{i32 7, !"uwtable", i32 2}
!4 = !{i32 7, !"frame-pointer", i32 2}
!5 = !{!"Ubuntu clang version 18.1.3 (1ubuntu1)"}
