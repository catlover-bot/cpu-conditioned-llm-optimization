; ModuleID = 'kernel.c'
source_filename = "kernel.c"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-i128:128-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

; Function Attrs: noinline nounwind uwtable
define dso_local void @kernel_gramschmidt(i32 noundef %m, i32 noundef %n, ptr noundef %A, ptr noundef %R, ptr noundef %Q) #0 {
entry:
  %cmp.mn = icmp sgt i32 %m, 0
  %cmp.nn = icmp sgt i32 %n, 0
  %n64 = sext i32 %n to i64
  %m64 = sext i32 %m to i64
  br label %for.cond

for.cond:                                         ; preds = %for.inc92, %entry
  %k = phi i32 [ 0, %entry ], [ %inc93, %for.inc92 ]
  %cmp = icmp slt i32 %k, %n
  br i1 %cmp, label %for.body, label %for.end94

for.body:                                         ; preds = %for.cond
  %k64 = sext i32 %k to i64
  br i1 %cmp.mn, label %for.cond6.preheader, label %for.end

for.cond6.preheader:                              ; preds = %for.body
  br label %for.body8

for.body8:                                        ; preds = %for.cond6.preheader, %for.body8
  %i6.phi = phi i64 [ 0, %for.cond6.preheader ], [ %i6.next, %for.body8 ]
  %nrm.phi = phi double [ 0.000000e+00, %for.cond6.preheader ], [ %add15, %for.body8 ]
  %rowoff6 = mul nsw i64 %i6.phi, %n64
  %aik.ptr = getelementptr inbounds double, ptr %A, i64 %rowoff6
  %aik.ptr2 = getelementptr inbounds double, ptr %aik.ptr, i64 %k64
  %aik = load double, ptr %aik.ptr2, align 8
  %mul = fmul double %aik, %aik
  %add15 = fadd double %nrm.phi, %mul
  %i6.next = add nuw nsw i64 %i6.phi, 1
  %cmp7 = icmp slt i64 %i6.next, %m64
  br i1 %cmp7, label %for.body8, label %for.end.loopexit

for.end.loopexit:                                 ; preds = %for.body8
  %nrm.lcssa = phi double [ %add15, %for.body8 ]
  br label %for.end

for.end:                                          ; preds = %for.end.loopexit, %for.body
  %nrm = phi double [ 0.000000e+00, %for.body ], [ %nrm.lcssa, %for.end.loopexit ]
  %call = call double @sqrt(double noundef %nrm) #2
  %rkk.rowoff = mul nsw i64 %k64, %n64
  %rkk.ptr = getelementptr inbounds double, ptr %R, i64 %rkk.rowoff
  %rkk.ptr2 = getelementptr inbounds double, ptr %rkk.ptr, i64 %k64
  store double %call, ptr %rkk.ptr2, align 8
  br i1 %cmp.mn, label %for.body22, label %for.end37

for.body22:                                       ; preds = %for.end, %for.body22
  %i22.phi = phi i64 [ 0, %for.end ], [ %i22.next, %for.body22 ]
  %rowoffA22 = mul nsw i64 %i22.phi, %n64
  %aptr22 = getelementptr inbounds double, ptr %A, i64 %rowoffA22
  %aptr22b = getelementptr inbounds double, ptr %aptr22, i64 %k64
  %aval22 = load double, ptr %aptr22b, align 8
  %div = fdiv double %aval22, %call
  %rowoffQ22 = mul nsw i64 %i22.phi, %n64
  %qptr22 = getelementptr inbounds double, ptr %Q, i64 %rowoffQ22
  %qptr22b = getelementptr inbounds double, ptr %qptr22, i64 %k64
  store double %div, ptr %qptr22b, align 8
  %i22.next = add nuw nsw i64 %i22.phi, 1
  %cmp21 = icmp slt i64 %i22.next, %m64
  br i1 %cmp21, label %for.body22, label %for.end37

for.end37:                                        ; preds = %for.body22, %for.end
  %kp1 = add nsw i32 %k, 1
  br label %for.cond39

for.cond39:                                       ; preds = %for.inc89, %for.end37
  %j = phi i32 [ %kp1, %for.end37 ], [ %inc90, %for.inc89 ]
  %cmp40 = icmp slt i32 %j, %n
  br i1 %cmp40, label %for.body41, label %for.end91

for.body41:                                       ; preds = %for.cond39
  %j64 = sext i32 %j to i64
  %rkj.ptr = getelementptr inbounds double, ptr %rkk.ptr, i64 %j64
  store double 0.000000e+00, ptr %rkj.ptr, align 8
  br i1 %cmp.mn, label %for.body48, label %for.end65

for.body48:                                       ; preds = %for.body41, %for.body48
  %i48.phi = phi i64 [ 0, %for.body41 ], [ %i48.next, %for.body48 ]
  %rowoffQ48 = mul nsw i64 %i48.phi, %n64
  %qptr48 = getelementptr inbounds double, ptr %Q, i64 %rowoffQ48
  %qptr48b = getelementptr inbounds double, ptr %qptr48, i64 %k64
  %qval48 = load double, ptr %qptr48b, align 8
  %rowoffA48 = mul nsw i64 %i48.phi, %n64
  %aptr48 = getelementptr inbounds double, ptr %A, i64 %rowoffA48
  %aptr48b = getelementptr inbounds double, ptr %aptr48, i64 %j64
  %aval48 = load double, ptr %aptr48b, align 8
  %mul57 = fmul double %qval48, %aval48
  %rkjcur = load double, ptr %rkj.ptr, align 8
  %add62 = fadd double %rkjcur, %mul57
  store double %add62, ptr %rkj.ptr, align 8
  %i48.next = add nuw nsw i64 %i48.phi, 1
  %cmp47 = icmp slt i64 %i48.next, %m64
  br i1 %cmp47, label %for.body48, label %for.end65

for.end65:                                        ; preds = %for.body48, %for.body41
  br i1 %cmp.mn, label %for.body68, label %for.end88

for.body68:                                       ; preds = %for.end65, %for.body68
  %i68.phi = phi i64 [ 0, %for.end65 ], [ %i68.next, %for.body68 ]
  %rowoffA68 = mul nsw i64 %i68.phi, %n64
  %aptr68 = getelementptr inbounds double, ptr %A, i64 %rowoffA68
  %aptr68b = getelementptr inbounds double, ptr %aptr68, i64 %j64
  %aval68 = load double, ptr %aptr68b, align 8
  %rowoffQ68 = mul nsw i64 %i68.phi, %n64
  %qptr68 = getelementptr inbounds double, ptr %Q, i64 %rowoffQ68
  %qptr68b = getelementptr inbounds double, ptr %qptr68, i64 %k64
  %qval68 = load double, ptr %qptr68b, align 8
  %rkjval68 = load double, ptr %rkj.ptr, align 8
  %mul81 = fmul double %qval68, %rkjval68
  %sub = fsub double %aval68, %mul81
  store double %sub, ptr %aptr68b, align 8
  %i68.next = add nuw nsw i64 %i68.phi, 1
  %cmp67 = icmp slt i64 %i68.next, %m64
  br i1 %cmp67, label %for.body68, label %for.end88

for.end88:                                        ; preds = %for.body68, %for.end65
  br label %for.inc89

for.inc89:                                        ; preds = %for.end88
  %inc90 = add nsw i32 %j, 1
  br label %for.cond39, !llvm.loop !8

for.end91:                                        ; preds = %for.cond39
  br label %for.inc92

for.inc92:                                        ; preds = %for.end91
  %inc93 = add nsw i32 %k, 1
  br label %for.cond, !llvm.loop !12

for.end94:                                        ; preds = %for.cond
  ret void
}

; Function Attrs: nounwind
declare double @sqrt(double noundef) #1

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
!6 = distinct !{!6, !7}
!7 = !{!"llvm.loop.mustprogress"}
!8 = distinct !{!8, !7}
!9 = distinct !{!9, !7}
!10 = distinct !{!10, !7}
!11 = distinct !{!11, !7}
!12 = distinct !{!12, !7}
