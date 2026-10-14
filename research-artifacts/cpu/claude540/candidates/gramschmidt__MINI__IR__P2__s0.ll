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
  br i1 %cmp.mn, label %for.body6.preheader, label %for.end

for.body6.preheader:                              ; preds = %for.body
  br label %for.body8

for.body8:                                        ; preds = %for.body6.preheader, %for.body8
  %i6.03 = phi i64 [ 0, %for.body6.preheader ], [ %inc.6, %for.body8 ]
  %nrm.02 = phi double [ 0.000000e+00, %for.body6.preheader ], [ %add15, %for.body8 ]
  %rowoff = mul nsw i64 %i6.03, %n64
  %elptr = getelementptr inbounds double, ptr %A, i64 %rowoff
  %elptr2 = getelementptr inbounds double, ptr %elptr, i64 %k64
  %aval = load double, ptr %elptr2, align 8
  %mul = fmul double %aval, %aval
  %add15 = fadd double %nrm.02, %mul
  %inc.6 = add nuw nsw i64 %i6.03, 1
  %cmp7 = icmp slt i64 %inc.6, %m64
  br i1 %cmp7, label %for.body8, label %for.end.loopexit

for.end.loopexit:                                 ; preds = %for.body8
  %nrm.lcssa = phi double [ %add15, %for.body8 ]
  br label %for.end

for.end:                                          ; preds = %for.end.loopexit, %for.body
  %nrm.final = phi double [ 0.000000e+00, %for.body ], [ %nrm.lcssa, %for.end.loopexit ]
  %call = call double @sqrt(double noundef %nrm.final) #2
  %Rk.rowoff = mul nsw i64 %k64, %n64
  %Rk.rowptr = getelementptr inbounds double, ptr %R, i64 %Rk.rowoff
  %Rkk.ptr = getelementptr inbounds double, ptr %Rk.rowptr, i64 %k64
  store double %call, ptr %Rkk.ptr, align 8
  br i1 %cmp.mn, label %for.body22.preheader, label %for.end37

for.body22.preheader:                             ; preds = %for.end
  br label %for.body22

for.body22:                                       ; preds = %for.body22.preheader, %for.body22
  %i22 = phi i64 [ 0, %for.body22.preheader ], [ %inc36, %for.body22 ]
  %A22.rowoff = mul nsw i64 %i22, %n64
  %A22.rowptr = getelementptr inbounds double, ptr %A, i64 %A22.rowoff
  %A22.elptr = getelementptr inbounds double, ptr %A22.rowptr, i64 %k64
  %aval22 = load double, ptr %A22.elptr, align 8
  %div = fdiv double %aval22, %call
  %Q22.rowoff = mul nsw i64 %i22, %n64
  %Q22.rowptr = getelementptr inbounds double, ptr %Q, i64 %Q22.rowoff
  %Q22.elptr = getelementptr inbounds double, ptr %Q22.rowptr, i64 %k64
  store double %div, ptr %Q22.elptr, align 8
  %inc36 = add nuw nsw i64 %i22, 1
  %cmp21 = icmp slt i64 %inc36, %m64
  br i1 %cmp21, label %for.body22, label %for.end37.loopexit

for.end37.loopexit:                               ; preds = %for.body22
  br label %for.end37

for.end37:                                        ; preds = %for.end37.loopexit, %for.end
  %j0 = add nsw i32 %k, 1
  br label %for.cond39

for.cond39:                                       ; preds = %for.inc89, %for.end37
  %j = phi i32 [ %j0, %for.end37 ], [ %inc90, %for.inc89 ]
  %cmp40 = icmp slt i32 %j, %n
  br i1 %cmp40, label %for.body41, label %for.end91

for.body41:                                       ; preds = %for.cond39
  %j64 = sext i32 %j to i64
  %Rk.rowoff41 = mul nsw i64 %k64, %n64
  %Rk.rowptr41 = getelementptr inbounds double, ptr %R, i64 %Rk.rowoff41
  %Rkj.ptr = getelementptr inbounds double, ptr %Rk.rowptr41, i64 %j64
  store double 0.000000e+00, ptr %Rkj.ptr, align 8
  br i1 %cmp.mn, label %for.body48.preheader, label %for.end65

for.body48.preheader:                             ; preds = %for.body41
  br label %for.body48

for.body48:                                       ; preds = %for.body48.preheader, %for.body48
  %i48 = phi i64 [ 0, %for.body48.preheader ], [ %inc64, %for.body48 ]
  %Q48.rowoff = mul nsw i64 %i48, %n64
  %Q48.rowptr = getelementptr inbounds double, ptr %Q, i64 %Q48.rowoff
  %Q48.elptr = getelementptr inbounds double, ptr %Q48.rowptr, i64 %k64
  %qval = load double, ptr %Q48.elptr, align 8
  %A48.rowoff = mul nsw i64 %i48, %n64
  %A48.rowptr = getelementptr inbounds double, ptr %A, i64 %A48.rowoff
  %A48.elptr = getelementptr inbounds double, ptr %A48.rowptr, i64 %j64
  %aval48 = load double, ptr %A48.elptr, align 8
  %mul57 = fmul double %qval, %aval48
  %rval = load double, ptr %Rkj.ptr, align 8
  %add62 = fadd double %rval, %mul57
  store double %add62, ptr %Rkj.ptr, align 8
  %inc64 = add nuw nsw i64 %i48, 1
  %cmp47 = icmp slt i64 %inc64, %m64
  br i1 %cmp47, label %for.body48, label %for.end65.loopexit

for.end65.loopexit:                               ; preds = %for.body48
  br label %for.end65

for.end65:                                        ; preds = %for.end65.loopexit, %for.body41
  %rval.after = load double, ptr %Rkj.ptr, align 8
  br i1 %cmp.mn, label %for.body68.preheader, label %for.end88

for.body68.preheader:                             ; preds = %for.end65
  br label %for.body68

for.body68:                                       ; preds = %for.body68.preheader, %for.body68
  %i68 = phi i64 [ 0, %for.body68.preheader ], [ %inc87, %for.body68 ]
  %A68.rowoff = mul nsw i64 %i68, %n64
  %A68.rowptr = getelementptr inbounds double, ptr %A, i64 %A68.rowoff
  %A68.elptr = getelementptr inbounds double, ptr %A68.rowptr, i64 %j64
  %aval68 = load double, ptr %A68.elptr, align 8
  %Q68.rowoff = mul nsw i64 %i68, %n64
  %Q68.rowptr = getelementptr inbounds double, ptr %Q, i64 %Q68.rowoff
  %Q68.elptr = getelementptr inbounds double, ptr %Q68.rowptr, i64 %k64
  %qval68 = load double, ptr %Q68.elptr, align 8
  %mul81 = fmul double %qval68, %rval.after
  %sub = fsub double %aval68, %mul81
  store double %sub, ptr %A68.elptr, align 8
  %inc87 = add nuw nsw i64 %i68, 1
  %cmp67 = icmp slt i64 %inc87, %m64
  br i1 %cmp67, label %for.body68, label %for.end88.loopexit

for.end88.loopexit:                               ; preds = %for.body68
  br label %for.end88

for.end88:                                        ; preds = %for.end88.loopexit, %for.end65
  br label %for.inc89

for.inc89:                                        ; preds = %for.end88
  %inc90 = add nsw i32 %j, 1
  br label %for.cond39, !llvm.loop !11

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
