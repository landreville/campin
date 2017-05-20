import { Pipe, PipeTransform } from "@angular/core";

export interface MapItem {
    key: string;
    value: any;
}

/**
 * This Pipe function will return a list of objects. Each object has
 * keys "key" and "value". This provides a sorted list of mappings
 * properties and values.
 *
 * For example if mapping is:
 * { myProp: "the value", otherProp: 10}
 * this will return:
 * [{key: "myProp", value: "the value"}, {key: "otherProp", value: 10}]
 *
 * Example usage:
 * <div *ngFor="let item of myObject | myMapItems"></div>
 */
@Pipe({
    name: 'myMapItems'
})
export class MapItems implements PipeTransform {

    public transform(mapping: any, ...args: any[]): MapItem[] {
        let items: MapItem[] = [];
        for (let key in mapping) {
            if (mapping.hasOwnProperty(key)) {
                items.push({key, value: mapping[key]});
            }
        }
        return items;
    }
}
