import { Attribute, Directive, forwardRef } from "@angular/core";
import { AbstractControl, NG_VALIDATORS, Validator } from "@angular/forms";

/**
 * Validator to ensure that date in one field is after the date in another field.
 *
 * Use as an attribute on the later date. The value must be the earlier field's reference.
 * Example:
 *
 * <my-date-picker name="startDate" #startDate="ngModel"></my-date-picker>
 *
 * <my-date-picker name="endDate" #endDate="ngModel" validateAfter="startDate">
 *     </my-date-picker>
 *
 */
@Directive({
    selector: '[validateAfter][formControlName],' +
    '[validateAfter][formControl],[validateAfter][ngModel]',
    providers: [
        {
            provide: NG_VALIDATORS,
            useExisting: forwardRef(() => AfterValidatorDirective),
            multi: true
        }
    ]
})
export class AfterValidatorDirective implements Validator {
    constructor(@Attribute('validateAfter') public validateAfter: string) {
    }

    public validate(control: AbstractControl): { [key: string]: any } {
        let value = control.value;
        let otherControl = control.root.get(this.validateAfter);
        let otherValue = otherControl.value;

        let afterDate = value ? value.jsdate : null;
        let beforeDate = otherValue ? otherValue.jsdate : null;

        if (afterDate && beforeDate && afterDate < beforeDate) {
            return {
                validateAfter: false
            };
        }
    }
}
